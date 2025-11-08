from __future__ import annotations

import argparse
import json
import logging
import warnings
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


class LogLevel(Enum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG


def deprecate_verbose(args: list[str], verbose: argparse.Action, parsed_args: argparse.Namespace):
    # If --verbose or -v were supplied, warn the user and interpret it as a DEBUG log level
    for option_string in verbose.option_strings:
        if option_string not in args:
            continue

        warnings.warn(
            "Argument %s is deprecated and will be interpreted as a DEBUG log level." % verbose.option_strings,
            stacklevel=2,
        )

        parsed_args.log_level = logging.DEBUG

        break

    del parsed_args.verbose


def parse_cli_args(args) -> dict:
    parser = argparse.ArgumentParser(
        prog="schemachange",
        description="Apply schema changes to a Snowflake account. Full readme at "
        "https://github.com/Snowflake-Labs/schemachange",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parent_parser = argparse.ArgumentParser(add_help=False)

    # Configuration file location arguments
    # Note: --schemachange-config-folder and --schemachange-config-file-name are consolidated
    # with their unprefixed variants for backward compatibility
    parent_parser.add_argument(
        "--config-folder",
        "--schemachange-config-folder",
        type=str,
        dest="config_folder",
        default=".",
        help="The folder to look in for the schemachange-config.yml file "
        "(the default is the current working directory). "
        "Can also be set via SCHEMACHANGE_CONFIG_FOLDER environment variable.",
        required=False,
    )
    parent_parser.add_argument(
        "--config-file-name",
        "--schemachange-config-file-name",
        type=str,
        dest="config_file_name",
        default="schemachange-config.yml",
        help="The schemachange config YAML file name. Must be in the directory supplied as the config-folder "
        "(Default: schemachange-config.yml). "
        "Can also be set via SCHEMACHANGE_CONFIG_FILE_NAME environment variable.",
        required=False,
    )

    # Schemachange application arguments with consolidated old/new forms
    parent_parser.add_argument(
        "-f",
        "--schemachange-root-folder",
        "--root-folder",
        type=str,
        dest="root_folder",
        help="The root folder for the database change scripts. "
        "Can also be set via SCHEMACHANGE_ROOT_FOLDER environment variable. "
        "(Deprecated alias: --root-folder)",
        required=False,
    )
    parent_parser.add_argument(
        "-m",
        "--schemachange-modules-folder",
        "--modules-folder",
        type=str,
        dest="modules_folder",
        help="The modules folder for jinja macros and templates to be used across multiple scripts. "
        "Can also be set via SCHEMACHANGE_MODULES_FOLDER environment variable. "
        "(Deprecated alias: --modules-folder)",
        required=False,
    )
    parent_parser.add_argument(
        "-V",
        "--schemachange-vars",
        "--vars",
        type=json.loads,
        dest="vars",
        help="Define values for the variables to replaced in change scripts, given in JSON format "
        '(e.g. {"variable1": "value1", "variable2": "value2"}). '
        "Can also be set via SCHEMACHANGE_VARS environment variable. "
        "(Deprecated alias: --vars)",
        required=False,
    )
    parent_parser.add_argument(
        "-L",
        "--schemachange-log-level",
        "--log-level",
        type=LogLevel,
        action=EnumAction,
        dest="log_level",
        default=logging.INFO,
        help="Set the log level. Defaults to INFO. "
        "Can also be set via SCHEMACHANGE_LOG_LEVEL environment variable. "
        "(Deprecated alias: --log-level)",
    )

    # Keep -v/--verbose deprecated as before
    verbose = parent_parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const=True,
        default=None,
        help="DEPRECATED: Use -L/--schemachange-log-level instead. Display verbose debugging details "
        "during execution (the default is False)",
        required=False,
    )

    subcommands = parser.add_subparsers(dest="subcommand")
    parser_deploy = subcommands.add_parser("deploy", parents=[parent_parser])

    # Snowflake connection arguments (these are correctly prefixed and not deprecated)
    parser_deploy.add_argument(
        "-a",
        "--snowflake-account",
        type=str,
        help="The name of the snowflake account (e.g. xy12345.east-us-2.azure, "
        "xy12345.east-us-2.azure.privatelink, org-accountname, org-accountname.privatelink). "
        "Can also be set via SNOWFLAKE_ACCOUNT environment variable.",
        required=False,
    )
    parser_deploy.add_argument(
        "-u",
        "--snowflake-user",
        type=str,
        help="The name of the snowflake user. " "Can also be set via SNOWFLAKE_USER environment variable.",
        required=False,
    )
    parser_deploy.add_argument(
        "-r",
        "--snowflake-role",
        type=str,
        help="The name of the default role to use. " "Can also be set via SNOWFLAKE_ROLE environment variable.",
        required=False,
    )
    parser_deploy.add_argument(
        "-w",
        "--snowflake-warehouse",
        type=str,
        help="The name of the default warehouse to use. Can be overridden in the change scripts. "
        "Can also be set via SNOWFLAKE_WAREHOUSE environment variable.",
        required=False,
    )
    parser_deploy.add_argument(
        "-d",
        "--snowflake-database",
        type=str,
        help="The name of the default database to use. Can be overridden in the change scripts. "
        "Can also be set via SNOWFLAKE_DATABASE environment variable.",
        required=False,
    )
    parser_deploy.add_argument(
        "-s",
        "--snowflake-schema",
        type=str,
        help="The name of the default schema to use. Can be overridden in the change scripts. "
        "Can also be set via SNOWFLAKE_SCHEMA environment variable.",
        required=False,
    )

    # Snowflake authentication arguments
    parser_deploy.add_argument(
        "--snowflake-authenticator",
        type=str,
        dest="authenticator",
        help="The authenticator method to use (e.g. 'snowflake', 'oauth', 'externalbrowser', "
        "'snowflake_jwt', or Okta URL). "
        "Can also be set via SNOWFLAKE_AUTHENTICATOR environment variable.",
        required=False,
    )
    parser_deploy.add_argument(
        "--snowflake-private-key-path",
        type=str,
        dest="private_key_path",
        help="Path to private key file for JWT (snowflake_jwt) authentication. "
        "Can also be set via SNOWFLAKE_PRIVATE_KEY_PATH environment variable.",
        required=False,
    )
    parser_deploy.add_argument(
        "--snowflake-private-key-passphrase",
        type=str,
        dest="private_key_passphrase",
        help="Passphrase for encrypted private key file. "
        "Can also be set via SNOWFLAKE_PRIVATE_KEY_PASSPHRASE environment variable.",
        required=False,
    )
    parser_deploy.add_argument(
        "--snowflake-token-file-path",
        type=str,
        dest="token_file_path",
        help="Path to OAuth token file (for use with --snowflake-authenticator oauth). "
        "Can also be set via SNOWFLAKE_TOKEN_FILE_PATH environment variable.",
        required=False,
    )

    # Schemachange deploy arguments with consolidated old/new forms
    parser_deploy.add_argument(
        "-c",
        "--schemachange-change-history-table",
        "--change-history-table",
        type=str,
        dest="change_history_table",
        help="Used to override the default name of the change history table "
        "(the default is METADATA.SCHEMACHANGE.CHANGE_HISTORY). "
        "Can also be set via SCHEMACHANGE_CHANGE_HISTORY_TABLE environment variable. "
        "(Deprecated alias: --change-history-table)",
        required=False,
    )
    parser_deploy.add_argument(
        "-ac",
        "--schemachange-autocommit",
        "--autocommit",
        action="store_const",
        const=True,
        default=None,
        dest="autocommit",
        help="Enable autocommit feature for DML commands (the default is False). "
        "Can also be set via SCHEMACHANGE_AUTOCOMMIT environment variable. "
        "(Deprecated alias: --autocommit)",
        required=False,
    )
    parser_deploy.add_argument(
        "-Q",
        "--schemachange-query-tag",
        "--query-tag",
        type=str,
        dest="query_tag",
        help="The string to add to the Snowflake QUERY_TAG session value for each query executed. "
        "Can also be set via SCHEMACHANGE_QUERY_TAG environment variable. "
        "(Deprecated alias: --query-tag)",
        required=False,
    )
    parser_deploy.add_argument(
        "-C",
        "--schemachange-connection-name",
        "--connection-name",
        type=str,
        dest="connection_name",
        help="Override the default connections.toml connection name. Other connection-related values will override these connection values. "
        "Can also be set via SCHEMACHANGE_CONNECTION_NAME environment variable. "
        "(Deprecated alias: --connection-name)",
        required=False,
    )
    parser_deploy.add_argument(
        "--schemachange-connections-file-path",
        "--connections-file-path",
        type=str,
        dest="connections_file_path",
        help="Override the default connections.toml file path at snowflake.connector.constants.CONNECTIONS_FILE (OS specific). "
        "Can also be set via SCHEMACHANGE_CONNECTIONS_FILE_PATH environment variable. "
        "(Deprecated alias: --connections-file-path)",
        required=False,
    )
    parser_deploy.add_argument(
        "--schemachange-create-change-history-table",
        "--create-change-history-table",
        action="store_const",
        const=True,
        default=None,
        dest="create_change_history_table",
        help="Create the change history schema and table, if they do not exist (the default is False). "
        "Can also be set via SCHEMACHANGE_CREATE_CHANGE_HISTORY_TABLE environment variable. "
        "(Deprecated alias: --create-change-history-table)",
        required=False,
    )
    parser_deploy.add_argument(
        "--schemachange-dry-run",
        "--dry-run",
        action="store_const",
        const=True,
        default=None,
        dest="dry_run",
        help="Run schemachange in dry run mode (the default is False). "
        "Can also be set via SCHEMACHANGE_DRY_RUN environment variable. "
        "(Deprecated alias: --dry-run)",
        required=False,
    )
    parser_deploy.add_argument(
        "--schemachange-version-number-validation-regex",
        "--version-number-validation-regex",
        type=str,
        dest="version_number_validation_regex",
        help="If supplied, version numbers will be validated with this regular expression. "
        "Can also be set via SCHEMACHANGE_VERSION_NUMBER_VALIDATION_REGEX environment variable. "
        "(Deprecated alias: --version-number-validation-regex)",
        required=False,
    )
    parser_deploy.add_argument(
        "--schemachange-raise-exception-on-ignored-versioned-script",
        "--raise-exception-on-ignored-versioned-script",
        action="store_const",
        const=True,
        default=None,
        dest="raise_exception_on_ignored_versioned_script",
        help="Raise an exception if an un-applied versioned script is ignored (the default is False). "
        "Can also be set via SCHEMACHANGE_RAISE_EXCEPTION_ON_IGNORED_VERSIONED_SCRIPT environment variable. "
        "(Deprecated alias: --raise-exception-on-ignored-versioned-script)",
        required=False,
    )

    parser_render = subcommands.add_parser(
        "render",
        description="Renders a script to the console, used to check and verify jinja output from scripts.",
        parents=[parent_parser],
    )
    parser_render.add_argument("script_path", type=str, help="Path to the script to render")

    # The original parameters did not support subcommands. Check if a subcommand has been supplied
    # if not default to deploy to match original behaviour.
    if len(args) == 0 or not any(subcommand in args[0].upper() for subcommand in ["DEPLOY", "RENDER"]):
        args = ["deploy"] + args

    parsed_args = parser.parse_args(args)

    # Handle deprecation warnings
    deprecate_verbose(args=args, verbose=verbose, parsed_args=parsed_args)

    parsed_kwargs = parsed_args.__dict__

    if "log_level" in parsed_kwargs and isinstance(parsed_kwargs["log_level"], Enum):
        parsed_kwargs["log_level"] = parsed_kwargs["log_level"].value

    parsed_kwargs["config_vars"] = {}
    if "vars" in parsed_kwargs:
        config_vars = parsed_kwargs.pop("vars")
        if config_vars is not None:
            parsed_kwargs["config_vars"] = config_vars

    if "verbose" in parsed_kwargs:
        parsed_kwargs["log_level"] = logging.DEBUG if parsed_kwargs["verbose"] else logging.INFO
        parsed_kwargs.pop("verbose")

    return {k: v for k, v in parsed_kwargs.items() if v is not None}
