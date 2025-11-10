import logging
import sys
from pathlib import Path

import structlog

from schemachange.config.DeployConfig import DeployConfig
from schemachange.config.parse_cli_args import parse_cli_args
from schemachange.config.RenderConfig import RenderConfig
from schemachange.config.utils import (
    get_all_snowflake_env_vars,
    get_connections_toml_session_parameters,
    get_schemachange_config_from_env,
    get_snowflake_account,
    get_snowflake_authenticator,
    get_snowflake_database,
    get_snowflake_default_connection_name,
    get_snowflake_private_key_passphrase,
    get_snowflake_private_key_path,
    get_snowflake_role,
    get_snowflake_schema,
    get_snowflake_session_parameters,
    get_snowflake_token_file_path,
    get_snowflake_user,
    get_snowflake_warehouse,
    load_yaml_config,
    validate_connections_file_permissions,
    validate_directory,
    validate_file_path,
)
from schemachange.config.VerifyConfig import VerifyConfig

logger = structlog.getLogger(__name__)


def get_env_config_kwargs() -> dict:
    """
    Get configuration from environment variables.

    Priority: CLI > ENV > YAML > connections.toml
    This function provides the ENV layer.

    Supports:
    - SCHEMACHANGE_* environment variables for schemachange-specific config
    - SNOWFLAKE_* environment variables for Snowflake connection parameters
    - Generic SNOWFLAKE_* pass-through for any connector parameter
    """
    env_kwargs = {}

    # 1. Get schemachange-specific config from SCHEMACHANGE_* env vars
    schemachange_env_config = get_schemachange_config_from_env()
    env_kwargs.update(schemachange_env_config)

    # 2. Get explicitly-mapped Snowflake connection parameters
    env_mapping = {
        "snowflake_account": get_snowflake_account,
        "snowflake_user": get_snowflake_user,
        "snowflake_role": get_snowflake_role,
        "snowflake_warehouse": get_snowflake_warehouse,
        "snowflake_database": get_snowflake_database,
        "snowflake_schema": get_snowflake_schema,
    }

    # Authentication parameters (stored for use in get_session_kwargs)
    auth_mapping = {
        "authenticator": get_snowflake_authenticator,
        "private_key_path": get_snowflake_private_key_path,
        "private_key_passphrase": get_snowflake_private_key_passphrase,
        "token_file_path": get_snowflake_token_file_path,
    }

    for param, env_getter in {**env_mapping, **auth_mapping}.items():
        env_value = env_getter()
        if env_value is not None:
            env_kwargs[param] = env_value

    # 3. Get session parameters from SNOWFLAKE_SESSION_PARAMETERS
    env_session_parameters = get_snowflake_session_parameters()
    if env_session_parameters:
        env_kwargs["session_parameters"] = env_session_parameters

    # 4. Get generic SNOWFLAKE_* environment variables for pass-through
    generic_snowflake_params = get_all_snowflake_env_vars()
    if generic_snowflake_params:
        # Store these for pass-through to Snowflake connector
        env_kwargs["additional_snowflake_params"] = generic_snowflake_params

    return env_kwargs


def get_yaml_config_kwargs(config_file_path: Path | None) -> dict:
    # load YAML inputs and convert kebabs to snakes
    kwargs = {k.replace("-", "_"): v for (k, v) in load_yaml_config(config_file_path).items()}

    if "verbose" in kwargs:
        if kwargs["verbose"]:
            kwargs["log_level"] = logging.DEBUG
        kwargs.pop("verbose")

    if "vars" in kwargs:
        kwargs["config_vars"] = kwargs.pop("vars")

    for deprecated_arg in [
        "snowflake_account",
        "snowflake_user",
        "snowflake_role",
        "snowflake_warehouse",
        "snowflake_database",
        "snowflake_schema",
    ]:
        if deprecated_arg in kwargs:
            logger.warning("DEPRECATED - Set in connections.toml instead", parameter=deprecated_arg)

    return {k: v for k, v in kwargs.items() if v is not None}


def get_merged_config(
    logger: structlog.BoundLogger,
) -> DeployConfig | RenderConfig | VerifyConfig:
    cli_kwargs = parse_cli_args(sys.argv[1:])
    logger.debug("cli_kwargs", **cli_kwargs)

    cli_config_vars = cli_kwargs.pop("config_vars")

    # Extract connections.toml path and connection name from CLI
    cli_connections_file_path = validate_file_path(file_path=cli_kwargs.pop("connections_file_path", None))
    cli_connection_name = cli_kwargs.pop("connection_name", None)

    config_folder = validate_directory(path=cli_kwargs.pop("config_folder", "."))
    config_file_name = cli_kwargs.pop("config_file_name")
    config_file_path = Path(config_folder) / config_file_name

    # Get YAML configuration (P3)
    yaml_kwargs = get_yaml_config_kwargs(
        config_file_path=config_file_path,
    )
    logger.debug("yaml_kwargs", **yaml_kwargs)

    # Get environment variable configuration (P2)
    env_kwargs = get_env_config_kwargs()
    logger.debug("env_kwargs", **env_kwargs)

    # Determine connections_file_path with priority: CLI > ENV > YAML
    # We pass this to the Snowflake connector, which will use it to load connections.toml
    connections_file_path = cli_connections_file_path
    if connections_file_path is None:
        connections_file_path = env_kwargs.pop("connections_file_path", None)
    if connections_file_path is None:
        connections_file_path = yaml_kwargs.pop("connections_file_path", None)
        if config_folder is not None and connections_file_path is not None:
            # noinspection PyTypeChecker
            connections_file_path = config_folder / connections_file_path

    # Allow missing connections file when using environment variable authentication
    if connections_file_path is not None:
        try:
            connections_file_path = validate_file_path(file_path=connections_file_path)
            # Validate file permissions for security
            validate_connections_file_permissions(connections_file_path)
        except ValueError:
            logger.debug(
                "connections-file-path specified but file does not exist, "
                "will attempt to use environment variables for authentication",
                connections_file_path=str(connections_file_path),
            )
            connections_file_path = None
            yaml_kwargs.pop("connection_name", None)

    # Determine connection_name with priority: CLI > ENV > YAML
    # We pass this to the Snowflake connector to select which profile to use from connections.toml
    connection_name = cli_connection_name
    if connection_name is None:
        connection_name = get_snowflake_default_connection_name()
    if connection_name is None:
        connection_name = yaml_kwargs.pop("connection_name", None)

    # Handle config_vars merging (CLI > ENV > YAML)
    yaml_config_vars = yaml_kwargs.pop("config_vars", None)
    if yaml_config_vars is None:
        yaml_config_vars = {}

    env_config_vars = env_kwargs.pop("config_vars", None)
    if env_config_vars is None:
        env_config_vars = {}

    config_vars = {
        **yaml_config_vars,  # P3: YAML (lowest priority)
        **env_config_vars,  # P2: ENV (middle priority)
        **cli_config_vars,  # P1: CLI (highest priority)
    }

    # Handle session_parameters merging (CLI > ENV > YAML > connections.toml)
    # Read connections.toml session parameters (P4: lowest priority)
    toml_session_params = get_connections_toml_session_parameters(connections_file_path, connection_name)

    # Extract session_parameters from YAML additional_snowflake_params if present
    yaml_session_params = yaml_kwargs.pop("session_parameters", None)
    if yaml_session_params is None:
        # Check if it's in additional_snowflake_params from YAML v2
        yaml_additional = yaml_kwargs.get("additional_snowflake_params", {})
        yaml_session_params = yaml_additional.pop("session_parameters", {}) if yaml_additional else {}
    if yaml_session_params is None:
        yaml_session_params = {}

    env_session_params = env_kwargs.pop("session_parameters", None)
    if env_session_params is None:
        env_session_params = {}

    cli_session_params = cli_kwargs.pop("session_parameters", None)
    if cli_session_params is None:
        cli_session_params = {}

    # Deep merge session_parameters (CLI > ENV > YAML > connections.toml)
    # Only explicitly-set parameters from connections.toml, not defaults
    # QUERY_TAG gets special treatment: append from all sources instead of override
    merged_session_params = {
        **toml_session_params,  # P4: connections.toml (lowest priority)
        **yaml_session_params,  # P3: YAML
        **env_session_params,  # P2: ENV
        **cli_session_params,  # P1: CLI (highest priority)
    }

    # Special handling for QUERY_TAG: append values from all sources
    query_tag_parts = []
    for params_dict in [toml_session_params, yaml_session_params, env_session_params, cli_session_params]:
        if "QUERY_TAG" in params_dict and params_dict["QUERY_TAG"]:
            query_tag_parts.append(str(params_dict["QUERY_TAG"]))

    if query_tag_parts:
        merged_session_params["QUERY_TAG"] = ";".join(query_tag_parts)

    logger.debug(
        "Merged session_parameters",
        toml_params=list(toml_session_params.keys()),
        yaml_params=list(yaml_session_params.keys()),
        env_params=list(env_session_params.keys()),
        cli_params=list(cli_session_params.keys()),
        final_merged=list(merged_session_params.keys()),
        query_tag_parts=query_tag_parts,
    )

    # Handle additional_snowflake_params merging (ENV > YAML)
    # These are parameters to pass through to snowflake.connector.connect()
    yaml_snowflake_params = yaml_kwargs.pop("additional_snowflake_params", {})
    env_snowflake_params = env_kwargs.pop("additional_snowflake_params", {})

    # Normalize YAML params to snake_case for consistent merging with ENV params
    # YAML v2 uses kebab-case, ENV uses snake_case
    normalized_yaml_params = {}
    for key, value in yaml_snowflake_params.items():
        snake_key = key.replace("-", "_")
        normalized_yaml_params[snake_key] = value

    # Merge with priority: ENV > YAML (both now in snake_case)
    additional_snowflake_params = {
        **normalized_yaml_params,
        **env_snowflake_params,
    }

    # Apply priority: P3 (YAML) < P2 (ENV) < P1 (CLI)
    # The Snowflake connector will load connections.toml (P4), and our merged params will override it
    # This gives us the effective priority: CLI > ENV > YAML > connections.toml
    kwargs = {
        "config_file_path": config_file_path,
        "config_vars": config_vars,
        **{k: v for k, v in yaml_kwargs.items() if v is not None},  # P3: YAML
        **{k: v for k, v in env_kwargs.items() if v is not None},  # P2: ENV
        **{k: v for k, v in cli_kwargs.items() if v is not None},  # P1: CLI (highest)
    }

    # Add merged session_parameters (CLI > ENV > YAML, will be merged with connections.toml in SnowflakeSession)
    if merged_session_params:
        kwargs["session_parameters"] = merged_session_params

    # Add additional_snowflake_params if any
    if additional_snowflake_params:
        kwargs["additional_snowflake_params"] = additional_snowflake_params

    # Pass connection_name and connections_file_path to let connector load connections.toml (P4)
    if connections_file_path is not None:
        kwargs["connections_file_path"] = connections_file_path
    if connection_name is not None:
        kwargs["connection_name"] = connection_name

    logger.debug("final kwargs", **kwargs)

    if cli_kwargs["subcommand"] == "deploy":
        return DeployConfig.factory(**kwargs)
    elif cli_kwargs["subcommand"] == "render":
        return RenderConfig.factory(**kwargs)
    elif cli_kwargs["subcommand"] == "verify":
        return VerifyConfig.factory(**kwargs)
    else:
        raise Exception(f"unhandled subcommand: {cli_kwargs['subcommand']}")
