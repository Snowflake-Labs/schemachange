import logging
import sys
from pathlib import Path

import structlog

from schemachange.config.DeployConfig import DeployConfig
from schemachange.config.parse_cli_args import parse_cli_args
from schemachange.config.RenderConfig import RenderConfig
from schemachange.config.utils import (
    get_all_snowflake_env_vars,
    get_connections_toml_parameters,
    get_schemachange_config_from_env,
    get_snowflake_account,
    get_snowflake_authenticator,
    get_snowflake_database,
    get_snowflake_default_connection_name,
    get_snowflake_home,
    get_snowflake_private_key_file,
    get_snowflake_private_key_file_pwd,
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

    # Authentication parameters (stored with snowflake_ prefix for consistency)
    auth_mapping = {
        "snowflake_authenticator": get_snowflake_authenticator,
        "snowflake_private_key_path": get_snowflake_private_key_path,  # Deprecated
        "snowflake_private_key_file": get_snowflake_private_key_file,  # Recommended
        "snowflake_private_key_passphrase": get_snowflake_private_key_passphrase,  # Deprecated
        "snowflake_private_key_file_pwd": get_snowflake_private_key_file_pwd,  # Recommended
        "snowflake_token_file_path": get_snowflake_token_file_path,
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

    # ============================================================================
    # FIRST PASS: Resolve connection_name and connections_file_path
    # These are proxies to read connection parameters from connections.toml
    # Apply precedence: CLI > ENV > YAML
    # If EITHER is specified, use connections.toml (with defaults for missing one)
    # If NEITHER is specified, skip connections.toml entirely
    # ============================================================================

    logger.info("=" * 80)
    logger.info("FIRST PASS: Resolving connections.toml configuration")
    logger.info("=" * 80)

    # Resolve connections_file_path with precedence: CLI > ENV > YAML
    resolved_connections_file_path = None
    connections_file_path_source = None

    if cli_connections_file_path is not None:
        resolved_connections_file_path = cli_connections_file_path
        connections_file_path_source = "CLI"
    elif "connections_file_path" in env_kwargs:
        resolved_connections_file_path = env_kwargs.pop("connections_file_path")
        connections_file_path_source = "ENV"
    elif "connections_file_path" in yaml_kwargs:
        resolved_connections_file_path = yaml_kwargs.pop("connections_file_path")
        connections_file_path_source = "YAML"

        # Only join with config_folder if path is relative (not absolute or tilde path)
        if config_folder is not None and resolved_connections_file_path is not None:
            path_obj = Path(resolved_connections_file_path)
            if not path_obj.is_absolute() and not str(resolved_connections_file_path).startswith("~"):
                resolved_connections_file_path = config_folder / resolved_connections_file_path
                logger.debug(f"Joined relative path with config_folder: {resolved_connections_file_path}")

    # Resolve connection_name with precedence: CLI > ENV > YAML
    resolved_connection_name = None
    connection_name_source = None

    if cli_connection_name is not None:
        resolved_connection_name = cli_connection_name
        connection_name_source = "CLI"
    else:
        env_connection_name = get_snowflake_default_connection_name()
        if env_connection_name is not None:
            resolved_connection_name = env_connection_name
            connection_name_source = "ENV"
        elif "connection_name" in yaml_kwargs:
            resolved_connection_name = yaml_kwargs.pop("connection_name")
            connection_name_source = "YAML"

    # Decision logic: Use connections.toml if EITHER connection_name OR connections_file_path is specified
    use_connections_toml = resolved_connection_name is not None or resolved_connections_file_path is not None

    if not use_connections_toml:
        # Neither specified - skip connections.toml entirely
        logger.info("No connection_name or connections_file_path specified")
        logger.info("Connection parameters will be resolved from CLI > ENV > YAML (connections.toml not used)")
        connections_file_path = None
        connection_name = None
    else:
        # At least one specified - use connections.toml with defaults for missing values

        # Default connection_name to 'default' if not specified
        if resolved_connection_name is None:
            connection_name = "default"
            logger.info("connection_name not specified, using default: 'default'")
        else:
            connection_name = resolved_connection_name
            logger.info(f"connection_name resolved from {connection_name_source}: {connection_name}")

        # Default connections_file_path to ~/.snowflake/connections.toml if not specified
        if resolved_connections_file_path is None:
            snowflake_home = get_snowflake_home()
            resolved_connections_file_path = Path(snowflake_home) / ".snowflake" / "connections.toml"
            connections_file_path_source = "default"
            logger.info(f"connections_file_path not specified, using default: {resolved_connections_file_path}")

        # Validate the resolved connections_file_path if we're using connections.toml
        if use_connections_toml:
            connections_file_path = None
            try:
                connections_file_path = validate_file_path(file_path=resolved_connections_file_path)
                validate_connections_file_permissions(connections_file_path)
                logger.info(
                    f"connections_file_path validated from {connections_file_path_source}: {connections_file_path}"
                )
            except ValueError as e:
                logger.warning(
                    f"connections_file_path from {connections_file_path_source} is invalid: {resolved_connections_file_path}",
                    error=str(e),
                )
                logger.info("Connection parameters will be resolved from CLI > ENV > YAML")
                connections_file_path = None
                connection_name = None

    logger.info("-" * 80)

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

    # Read ALL parameters from connections.toml using resolved connection_name and connections_file_path
    # These parameters will be P4 (lowest priority) in the merge chain
    # Only read if FIRST PASS determined we should use connections.toml
    toml_connection_params = {}
    toml_session_params = {}

    if connections_file_path is not None and connection_name is not None:
        logger.info(f"Reading connection '{connection_name}' from {connections_file_path}")
        toml_connection_params, toml_session_params = get_connections_toml_parameters(
            connections_file_path, connection_name
        )

        if toml_connection_params or toml_session_params:
            logger.info(
                f"Successfully loaded {len(toml_connection_params)} connection parameter(s) "
                f"and {len(toml_session_params)} session parameter(s) from connections.toml"
            )
            logger.debug(
                "Parameters from connections.toml",
                connection_param_keys=list(toml_connection_params.keys()),
                session_param_keys=list(toml_session_params.keys()),
            )
        else:
            logger.warning(f"Connection '{connection_name}' not found or has no parameters in {connections_file_path}")
            logger.info("Connection parameters will be resolved from CLI > ENV > YAML")

    logger.info("=" * 80)
    logger.info("")

    # Merge toml connection parameters into yaml_kwargs for proper precedence
    # Priority: CLI > ENV > YAML > connections.toml
    # We merge toml params as the base layer (P4)
    # Note: connections.toml uses "account", "user" etc., but config expects "snowflake_account", "snowflake_user"

    # Debug: Show existing values before merging
    logger.debug(
        "Existing snowflake parameters before merging connections.toml",
        yaml_snowflake_params={k: v for k, v in yaml_kwargs.items() if k.startswith("snowflake_")},
        env_snowflake_params={k: v for k, v in env_kwargs.items() if k.startswith("snowflake_")},
        cli_snowflake_params={k: v for k, v in cli_kwargs.items() if k.startswith("snowflake_")},
    )

    # Add snowflake_ prefix to ALL Snowflake connector parameters for internal consistency
    # The prefix will be stripped later when building connect_kwargs
    merged_count = 0
    skipped_params = []
    for key, value in toml_connection_params.items():
        # All parameters from connections.toml get snowflake_ prefix internally
        config_key = f"snowflake_{key}"

        # Only set if not already set by higher priority source
        if config_key not in yaml_kwargs and config_key not in env_kwargs and config_key not in cli_kwargs:
            yaml_kwargs[config_key] = value
            merged_count += 1
        else:
            skipped_params.append(key)

    # Handle deprecated parameter name mapping from connections.toml (backwards compatibility)
    # private_key_path -> private_key_file
    # private_key_passphrase -> private_key_file_pwd
    # Only apply mapping if the deprecated name came from connections.toml (not overridden by higher priority sources)

    if (
        "snowflake_private_key_path" in yaml_kwargs
        and "snowflake_private_key_file" not in yaml_kwargs
        and "snowflake_private_key_path" not in env_kwargs
        and "snowflake_private_key_path" not in cli_kwargs
    ):
        # This private_key_path came from connections.toml (lowest priority) - show deprecation warning
        logger.warning(
            "DEPRECATION WARNING: 'private_key_path' in connections.toml is deprecated. "
            "Please use 'private_key_file' instead to match the Snowflake Python Connector parameter name. "
            "'private_key_path' will be removed in a future version."
        )
        # Map private_key_path -> private_key_file for internal consistency
        yaml_kwargs["snowflake_private_key_file"] = yaml_kwargs.pop("snowflake_private_key_path")

    if (
        "snowflake_private_key_passphrase" in yaml_kwargs
        and "snowflake_private_key_file_pwd" not in yaml_kwargs
        and "snowflake_private_key_passphrase" not in env_kwargs
    ):
        # This private_key_passphrase came from connections.toml (lowest priority) - show deprecation warning
        logger.warning(
            "DEPRECATION WARNING: 'private_key_passphrase' in connections.toml is deprecated. "
            "Please use 'private_key_file_pwd' instead to match the Snowflake Python Connector parameter name. "
            "'private_key_passphrase' will be removed in a future version."
        )
        # Map private_key_passphrase -> private_key_file_pwd for internal consistency
        yaml_kwargs["snowflake_private_key_file_pwd"] = yaml_kwargs.pop("snowflake_private_key_passphrase")

    logger.debug(
        "Merged connections.toml connection parameters",
        merged_count=merged_count,
        skipped_params=skipped_params,
        toml_connection_params_keys=list(toml_connection_params.keys()),
        toml_session_params_keys=list(toml_session_params.keys()),
    )

    # Handle session_parameters merging (CLI > ENV > YAML > connections.toml)
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

    # Extract well-known Snowflake connector parameters from YAML's snowflake section
    # and add them to yaml_kwargs with snowflake_ prefix for consistent handling
    well_known_params = [
        "account",
        "user",
        "role",
        "warehouse",
        "database",
        "schema",
        "authenticator",
        "private_key_path",
        "private_key_passphrase",
        "token_file_path",
    ]

    for param in well_known_params:
        if param in normalized_yaml_params:
            yaml_kwargs[f"snowflake_{param}"] = normalized_yaml_params.pop(param)

    # Remaining normalized_yaml_params are generic pass-through parameters
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

    # Add merged session_parameters (already includes connections.toml params at P4)
    if merged_session_params:
        kwargs["session_parameters"] = merged_session_params

    # Add additional_snowflake_params if any
    if additional_snowflake_params:
        kwargs["additional_snowflake_params"] = additional_snowflake_params

    # Pass connection_name and connections_file_path to config objects for logging/informational purposes
    # These will NOT be passed to snowflake.connector.connect() - we've already merged all params above
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
