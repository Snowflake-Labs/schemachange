import logging
import sys
from pathlib import Path
from typing import Union, Optional

import structlog

from schemachange.config.DeployConfig import DeployConfig
from schemachange.config.RenderConfig import RenderConfig
from schemachange.config.parse_cli_args import parse_cli_args
from schemachange.config.utils import (
    get_snowflake_account,
    get_snowflake_authenticator,
    get_snowflake_connections_file_path,
    get_snowflake_database,
    get_snowflake_default_connection_name,
    get_snowflake_private_key_passphrase,
    get_snowflake_private_key_path,
    get_snowflake_role,
    get_snowflake_schema,
    get_snowflake_token_file_path,
    get_snowflake_user,
    get_snowflake_warehouse,
    load_yaml_config,
    validate_directory,
    validate_file_path,
)


def get_env_config_kwargs() -> dict:
    """
    Get configuration from environment variables.

    Priority: CLI > ENV > YAML > connections.toml
    This function provides the ENV layer.
    """
    env_kwargs = {}

    # Basic connection parameters
    env_mapping = {
        "snowflake_account": get_snowflake_account,
        "snowflake_user": get_snowflake_user,
        "snowflake_role": get_snowflake_role,
        "snowflake_warehouse": get_snowflake_warehouse,
        "snowflake_database": get_snowflake_database,
        "snowflake_schema": get_snowflake_schema,
        "connections_file_path": get_snowflake_connections_file_path,
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

    return env_kwargs


def get_yaml_config_kwargs(config_file_path: Optional[Path]) -> dict:
    # load YAML inputs and convert kebabs to snakes
    kwargs = {
        k.replace("-", "_"): v for (k, v) in load_yaml_config(config_file_path).items()
    }

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
            sys.stderr.write(
                f"DEPRECATED - Set in connections.toml instead: {deprecated_arg}\n"
            )

    return {k: v for k, v in kwargs.items() if v is not None}


def get_merged_config(
    logger: structlog.BoundLogger,
) -> Union[DeployConfig, RenderConfig]:
    cli_kwargs = parse_cli_args(sys.argv[1:])
    logger.debug("cli_kwargs", **cli_kwargs)

    cli_config_vars = cli_kwargs.pop("config_vars")

    # Extract connections.toml path and connection name from CLI
    cli_connections_file_path = validate_file_path(
        file_path=cli_kwargs.pop("connections_file_path", None)
    )
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

    # Handle config_vars
    yaml_config_vars = yaml_kwargs.pop("config_vars", None)
    if yaml_config_vars is None:
        yaml_config_vars = {}

    config_vars = {
        **yaml_config_vars,
        **cli_config_vars,
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
    else:
        raise Exception(f"unhandled subcommand: {cli_kwargs['subcommand']}")
