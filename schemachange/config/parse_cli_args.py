from __future__ import annotations

import argparse
import json
import logging
from enum import Enum

import structlog

logger = structlog.getLogger(__name__)


class EnumAction(argparse.Action):
    """
    Argparse action for handling Enums

    Thanks to Tim!
    https://stackoverflow.com/a/60750535
    """

    def __init__(self, **kwargs):
        # Pop off the type value
        enum_type = kwargs.pop("type", None)

        # Ensure an Enum subclass is provided
        if enum_type is None:
            raise ValueError("type must be assigned an Enum when using EnumAction")
        # noinspection PyTypeChecker
        if not issubclass(enum_type, Enum):
            raise TypeError("type must be an Enum when using EnumAction")

        # Generate choices from the Enum
        kwargs.setdefault("choices", tuple(e.name for e in enum_type))

        super().__init__(**kwargs)

        self._enum = enum_type

    def __call__(self, parser, namespace, values, option_string=None):
        # Convert value back into an Enum
        value = self._enum[values]
        setattr(namespace, self.dest, value)


def parse_cli_args(args) -> dict:
    parser = argparse.ArgumentParser(
        prog="schemachange",
        description="Apply schema changes to a Snowflake account. Full readme at "
        "https://github.com/Snowflake-Labs/schemachange",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--config-folder",
        type=str,
        default=".",
        help="The folder to look in for the schemachange-config.yml file "
        "(the default is the current working directory)",
        required=False,
    )
    parent_parser.add_argument(
        "--config-file-name",
        type=str,
        default="schemachange-config.yml",
        help="The schemachange config YAML file name. Must be in the directory supplied as the config-folder "
        "(Default: schemachange-config.yml)",
        required=False,
    )
    parent_parser.add_argument(
        "-f",
        "--root-folder",
        type=str,
        help="The root folder for the database change scripts",
        required=False,
    )
    parent_parser.add_argument(
        "-m",
        "--modules-folder",
        type=str,
        help="The modules folder for jinja macros and templates to be used across multiple scripts",
        required=False,
    )
    parent_parser.add_argument(
        "--vars",
        type=json.loads,
        help='Define values for the variables to replaced in change scripts, given in JSON format (e.g. {"variable1": '
        '"value1", "variable2": "value2"})',
        required=False,
    )
    parent_parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const=True,
        default=None,
        help="Display verbose debugging details during execution (the default is False)",
        required=False,
    )

    subcommands = parser.add_subparsers(dest="subcommand")
    parser_deploy = subcommands.add_parser("deploy", parents=[parent_parser])

    parser_deploy.add_argument(
        "-a",
        "--snowflake-account",
        type=str,
        help="The name of the snowflake account (e.g. xy12345.east-us-2.azure)",
        required=False,
    )
    parser_deploy.add_argument(
        "-u",
        "--snowflake-user",
        type=str,
        help="The name of the snowflake user",
        required=False,
    )
    parser_deploy.add_argument(
        "-r",
        "--snowflake-role",
        type=str,
        help="The name of the default role to use",
        required=False,
    )
    parser_deploy.add_argument(
        "-w",
        "--snowflake-warehouse",
        type=str,
        help="The name of the default warehouse to use. Can be overridden in the change scripts.",
        required=False,
    )
    parser_deploy.add_argument(
        "-d",
        "--snowflake-database",
        type=str,
        help="The name of the default database to use. Can be overridden in the change scripts.",
        required=False,
    )
    parser_deploy.add_argument(
        "-s",
        "--snowflake-schema",
        type=str,
        help="The name of the default schema to use. Can be overridden in the change scripts.",
        required=False,
    )
    parser_deploy.add_argument(
        "-A",
        "--snowflake-authenticator",
        type=str,
        help="The Snowflake Authenticator to use. One of snowflake, oauth, externalbrowser, or https://<okta_account_name>.okta.com",
        required=False,
    )
    parser_deploy.add_argument(
        "-k",
        "--snowflake-private-key-path",
        type=str,
        help="Path to file containing private key.",
        required=False,
    )
    parser_deploy.add_argument(
        "-t",
        "--snowflake-token-path",
        type=str,
        help="Path to the file containing the OAuth token to be used when authenticating with Snowflake.",
        required=False,
    )
    parser_deploy.add_argument(
        "--connections-file-path",
        type=str,
        help="Override the default connections.toml file path at snowflake.connector.constants.CONNECTIONS_FILE (OS specific)",
        required=False,
    )
    parser_deploy.add_argument(
        "--connection-name",
        type=str,
        help="Override the default connections.toml connection name. Other connection-related values will override these connection values.",
        required=False,
    )
    parser_deploy.add_argument(
        "-c",
        "--change-history-table",
        type=str,
        help="Used to override the default name of the change history table (the default is "
        "METADATA.SCHEMACHANGE.CHANGE_HISTORY)",
        required=False,
    )
    parser_deploy.add_argument(
        "--create-change-history-table",
        action="store_const",
        const=True,
        default=None,
        help="Create the change history schema and table, if they do not exist (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "-ac",
        "--autocommit",
        action="store_const",
        const=True,
        default=None,
        help="Enable autocommit feature for DML commands (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "--dry-run",
        action="store_const",
        const=True,
        default=None,
        help="Run schemachange in dry run mode (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "--query-tag",
        type=str,
        help="The string to add to the Snowflake QUERY_TAG session value for each query executed",
        required=False,
    )
    parser_render = subcommands.add_parser(
        "render",
        description="Renders a script to the console, used to check and verify jinja output from scripts.",
        parents=[parent_parser],
    )
    parser_render.add_argument(
        "script_path", type=str, help="Path to the script to render"
    )

    # The original parameters did not support subcommands. Check if a subcommand has been supplied
    # if not default to deploy to match original behaviour.
    if len(args) == 0 or not any(
        subcommand in args[0].upper() for subcommand in ["DEPLOY", "RENDER"]
    ):
        args = ["deploy"] + args

    parsed_args = parser.parse_args(args)

    parsed_kwargs = parsed_args.__dict__

    if "log_level" in parsed_kwargs and isinstance(parsed_kwargs["log_level"], Enum):
        parsed_kwargs["log_level"] = parsed_kwargs["log_level"].value

    parsed_kwargs["config_vars"] = {}
    if "vars" in parsed_kwargs:
        config_vars = parsed_kwargs.pop("vars")
        if config_vars is not None:
            parsed_kwargs["config_vars"] = config_vars

    if "verbose" in parsed_kwargs:
        parsed_kwargs["log_level"] = (
            logging.DEBUG if parsed_kwargs["verbose"] else logging.INFO
        )
        parsed_kwargs.pop("verbose")

    return {k: v for k, v in parsed_kwargs.items() if v is not None}
