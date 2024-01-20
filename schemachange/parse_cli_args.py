from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from enum import Enum

import structlog

from schemachange.utils import EnumAction

logger = structlog.getLogger(__name__)


class LogLevel(Enum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG


def deprecate_verbose(
    args: list[str], verbose: argparse.Action, parsed_args: argparse.Namespace
):
    # If --verbose or -v were supplied, warn the user and interpret it as a
    for option_string in verbose.option_strings:
        if option_string not in args:
            continue

        warnings.warn(
            "Argument %s is deprecated and will be interpreted as a DEBUG log level."
            % verbose.option_strings
        )

        parsed_args.log_level = logging.DEBUG

        break

    del parsed_args.verbose


def parse_cli_args(args) -> argparse.Namespace:
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
        "--log-level",
        type=LogLevel,
        action=EnumAction,
        default=logging.INFO,
        help="Set the log level. Defaults to INFO.",
    )
    verbose = parent_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="DEPRECATED: Use --log-level instead. Display verbose debugging details "
        "during execution (the default is False)",
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
        "-c",
        "--change-history-table",
        type=str,
        help="Used to override the default name of the change history table (the default is "
        "METADATA.SCHEMACHANGE.CHANGE_HISTORY)",
        required=False,
    )
    parser_deploy.add_argument(
        "--create-change-history-table",
        action="store_true",
        help="Create the change history schema and table, if they do not exist (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "-ac",
        "--autocommit",
        action="store_true",
        help="Enable autocommit feature for DML commands (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "--dry-run",
        action="store_true",
        help="Run schemachange in dry run mode (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "--query-tag",
        type=str,
        help="The string to add to the Snowflake QUERY_TAG session value for each query executed",
        required=False,
    )
    parser_deploy.add_argument(
        "--oauth-config",
        type=json.loads,
        help='Define values for the variables to Make Oauth Token requests  (e.g. {"token-provider-url": '
        '"https//...", "token-request-payload": {"client_id": "GUID_xyz",...},... })',
        required=False,
    )
    parser_deploy.add_argument(
        "--version_number_validation_regex",
        type=str,
        help="If supplied, version numbers will be validated with this regular expression.",
        required=False,
    )
    parser_deploy.add_argument(
        "--raise-exception-on-ignored-versioned-migration",
        action="store_true",
        help="Raise an exception if an un-applied versioned migration is ignored (the default is False)",
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

    deprecate_verbose(args=args, verbose=verbose, parsed_args=parsed_args)

    return parsed_args


if __name__ == "__main__":
    parse_cli_args(sys.argv[1:])
