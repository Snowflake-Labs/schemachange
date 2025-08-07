import logging
import sys
from pathlib import Path
from typing import Union, Optional

import structlog

from schemachange.config.DeployConfig import DeployConfig
from schemachange.config.RenderConfig import RenderConfig
from schemachange.config.parse_cli_args import parse_cli_args
from schemachange.config.utils import (
    load_yaml_config,
    validate_directory,
    validate_file_path,
)


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

    connections_file_path = validate_file_path(
        file_path=cli_kwargs.pop("connections_file_path", None)
    )

    connection_name = cli_kwargs.pop("connection_name", None)

    config_folder = validate_directory(path=cli_kwargs.pop("config_folder", "."))
    config_file_name = cli_kwargs.pop("config_file_name")
    config_file_path = Path(config_folder) / config_file_name

    yaml_kwargs = get_yaml_config_kwargs(
        config_file_path=config_file_path,
    )
    logger.debug("yaml_kwargs", **yaml_kwargs)

    yaml_config_vars = yaml_kwargs.pop("config_vars", None)
    if yaml_config_vars is None:
        yaml_config_vars = {}

    if connections_file_path is None:
        connections_file_path = yaml_kwargs.pop("connections_file_path", None)
        if config_folder is not None and connections_file_path is not None:
            # noinspection PyTypeChecker
            connections_file_path = config_folder / connections_file_path

        connections_file_path = validate_file_path(file_path=connections_file_path)

    if connection_name is None:
        connection_name = yaml_kwargs.pop("connection_name", None)

    config_vars = {
        **yaml_config_vars,
        **cli_config_vars,
    }

    # override the YAML config with the CLI configuration
    kwargs = {
        "config_file_path": config_file_path,
        "config_vars": config_vars,
        **{k: v for k, v in yaml_kwargs.items() if v is not None},
        **{k: v for k, v in cli_kwargs.items() if v is not None},
    }
    if "continue_all_on_error" in kwargs:
        if kwargs["continue_all_on_error"]:
            kwargs["continue_versioned_on_error"] = True
            kwargs["continue_repeatable_on_error"] = True
            kwargs["continue_always_on_error"] = True
        del kwargs["continue_all_on_error"]
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
