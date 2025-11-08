from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from enum import Enum

import structlog

logger = structlog.getLogger(__name__)


class DeprecateSchemachangeArgAction(argparse.Action):
    """
    Action for deprecated unprefixed schemachange arguments.
    Shows migration path to new prefixed arguments with short forms.
    """

    def __init__(self, *args, new_arg_long=None, new_arg_short=None, **kwargs):
        self.call_count = 0
        self.new_arg_long = new_arg_long
        self.new_arg_short = new_arg_short

        if "help" in kwargs:
            migration_msg = f"Use {new_arg_short} or {new_arg_long}" if new_arg_short else f"Use {new_arg_long}"
            kwargs["help"] = f'[DEPRECATED - {migration_msg} instead.] {kwargs["help"]}'
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if self.call_count == 0:
            # Build migration message with examples
            if self.new_arg_short:
                migration_examples = (
                    f"  New: {self.new_arg_short} {values if not isinstance(values, bool) else ''}\n"
                    f"  New: {self.new_arg_long} {values if not isinstance(values, bool) else ''}"
                )
                migration_msg = f"use {self.new_arg_short} or {self.new_arg_long}"
            else:
                migration_examples = f"  New: {self.new_arg_long} {values if not isinstance(values, bool) else ''}"
                migration_msg = f"use {self.new_arg_long}"

            env_var = f"SCHEMACHANGE_{self.dest.upper()}"
            env_example = (
                f"  Env: export {env_var}={values if isinstance(values, str) else ('true' if values else 'false')}"
            )

            sys.stderr.write(
                f"\nDEPRECATION WARNING: {option_string} is deprecated.\n"
                f"Please {migration_msg} or set {env_var} environment variable instead.\n"
                f"Examples:\n"
                f"  Old: {option_string} {values if not isinstance(values, bool) else ''}\n"
                f"{migration_examples}\n"
                f"{env_example}\n\n"
            )
        self.call_count += 1
        setattr(namespace, self.dest, values)


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
    # If --verbose or -v were supplied, warn the user and interpret it as a
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


def deprecate_log_level(args: list[str]):
    """
    Check if old --log-level argument was used and show deprecation warning.
    This needs special handling since --log-level uses EnumAction.
    """
    if "--log-level" in args:
        # Find the log level value from args
        try:
            log_level_idx = args.index("--log-level")
            log_level_value = args[log_level_idx + 1] if log_level_idx + 1 < len(args) else "INFO"
        except (ValueError, IndexError):
            log_level_value = "INFO"

        sys.stderr.write(
            f"\nDEPRECATION WARNING: --log-level is deprecated.\n"
            f"Please use -L or --schemachange-log-level or set SCHEMACHANGE_LOG_LEVEL environment variable instead.\n"
            f"Examples:\n"
            f"  Old: --log-level {log_level_value}\n"
            f"  New: -L {log_level_value}\n"
            f"  New: --schemachange-log-level {log_level_value}\n"
            f"  Env: export SCHEMACHANGE_LOG_LEVEL={log_level_value}\n\n"
        )


def parse_cli_args(args) -> dict:
    parser = argparse.ArgumentParser(
        prog="schemachange",
        description="Apply schema changes to a Snowflake account. Full readme at "
        "https://github.com/Snowflake-Labs/schemachange",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parent_parser = argparse.ArgumentParser(add_help=False)

    # Register custom actions
    parent_parser.register("action", "deprecate_schemachange", DeprecateSchemachangeArgAction)

    # Configuration file location arguments (no prefix needed - these are meta-config)
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

    # NEW: Prefixed schemachange arguments with short forms
    parent_parser.add_argument(
        "-f",
        "--schemachange-root-folder",
        type=str,
        dest="root_folder",
        help="The root folder for the database change scripts",
        required=False,
    )
    parent_parser.add_argument(
        "-m",
        "--schemachange-modules-folder",
        type=str,
        dest="modules_folder",
        help="The modules folder for jinja macros and templates to be used across multiple scripts",
        required=False,
    )
    parent_parser.add_argument(
        "-V",
        "--schemachange-vars",
        type=json.loads,
        dest="vars",
        help='Define values for the variables to replaced in change scripts, given in JSON format (e.g. {"variable1": '
        '"value1", "variable2": "value2"})',
        required=False,
    )
    parent_parser.add_argument(
        "-L",
        "--schemachange-log-level",
        type=LogLevel,
        action=EnumAction,
        dest="log_level",
        default=logging.INFO,
        help="Set the log level. Defaults to INFO.",
    )
    parent_parser.add_argument(
        "--schemachange-config-folder",
        type=str,
        dest="config_folder",
        help="The folder to look in for the schemachange-config.yml file "
        "(the default is the current working directory)",
        required=False,
    )
    parent_parser.add_argument(
        "--schemachange-config-file-name",
        type=str,
        dest="config_file_name",
        help="The schemachange config YAML file name. Must be in the directory supplied as the config-folder "
        "(Default: schemachange-config.yml)",
        required=False,
    )

    # DEPRECATED: Old unprefixed arguments (kept for backward compatibility)
    parent_parser.add_argument(
        "--root-folder",
        type=str,
        dest="root_folder",
        action="deprecate_schemachange",
        new_arg_short="-f",
        new_arg_long="--schemachange-root-folder",
        help="The root folder for the database change scripts",
        required=False,
    )
    parent_parser.add_argument(
        "--modules-folder",
        type=str,
        dest="modules_folder",
        action="deprecate_schemachange",
        new_arg_short="-m",
        new_arg_long="--schemachange-modules-folder",
        help="The modules folder for jinja macros and templates to be used across multiple scripts",
        required=False,
    )
    parent_parser.add_argument(
        "--vars",
        type=json.loads,
        dest="vars",
        action="deprecate_schemachange",
        new_arg_short="-V",
        new_arg_long="--schemachange-vars",
        help='Define values for the variables to replaced in change scripts, given in JSON format (e.g. {"variable1": '
        '"value1", "variable2": "value2"})',
        required=False,
    )
    parent_parser.add_argument(
        "--log-level",
        type=LogLevel,
        action=EnumAction,
        dest="log_level",
        # Note: This will need custom handling since it uses EnumAction
        help="[DEPRECATED - Use -L or --schemachange-log-level instead.] Set the log level. Defaults to INFO.",
        required=False,
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

    # Register custom actions for deploy subcommand
    parser_deploy.register("action", "deprecate_schemachange", DeprecateSchemachangeArgAction)

    # Snowflake connection arguments (NO LONGER DEPRECATED - these are correctly prefixed)
    parser_deploy.add_argument(
        "-a",
        "--snowflake-account",
        type=str,
        help="The name of the snowflake account (e.g. xy12345.east-us-2.azure, xy12345.east-us-2.azure.privatelink, org-accountname, org-accountname.privatelink)",
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

    # Snowflake authentication arguments
    parser_deploy.add_argument(
        "--snowflake-authenticator",
        type=str,
        dest="authenticator",
        help="The authenticator method to use (e.g. 'snowflake', 'oauth', 'externalbrowser', 'snowflake_jwt', or Okta URL)",
        required=False,
    )
    parser_deploy.add_argument(
        "--snowflake-private-key-path",
        type=str,
        dest="private_key_path",
        help="Path to private key file for JWT (snowflake_jwt) authentication",
        required=False,
    )
    parser_deploy.add_argument(
        "--snowflake-private-key-passphrase",
        type=str,
        dest="private_key_passphrase",
        help="Passphrase for encrypted private key file",
        required=False,
    )
    parser_deploy.add_argument(
        "--snowflake-token-file-path",
        type=str,
        dest="token_file_path",
        help="Path to OAuth token file (for use with --snowflake-authenticator oauth)",
        required=False,
    )

    # NEW: Prefixed schemachange arguments for deploy
    parser_deploy.add_argument(
        "-c",
        "--schemachange-change-history-table",
        type=str,
        dest="change_history_table",
        help="Used to override the default name of the change history table (the default is "
        "METADATA.SCHEMACHANGE.CHANGE_HISTORY)",
        required=False,
    )
    parser_deploy.add_argument(
        "-ac",
        "--schemachange-autocommit",
        action="store_const",
        const=True,
        default=None,
        dest="autocommit",
        help="Enable autocommit feature for DML commands (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "-Q",
        "--schemachange-query-tag",
        type=str,
        dest="query_tag",
        help="The string to add to the Snowflake QUERY_TAG session value for each query executed",
        required=False,
    )
    parser_deploy.add_argument(
        "-C",
        "--schemachange-connection-name",
        type=str,
        dest="connection_name",
        help="Override the default connections.toml connection name. Other connection-related values will override these connection values.",
        required=False,
    )
    parser_deploy.add_argument(
        "--schemachange-connections-file-path",
        type=str,
        dest="connections_file_path",
        help="Override the default connections.toml file path at snowflake.connector.constants.CONNECTIONS_FILE (OS specific)",
        required=False,
    )
    parser_deploy.add_argument(
        "--schemachange-create-change-history-table",
        action="store_const",
        const=True,
        default=None,
        dest="create_change_history_table",
        help="Create the change history schema and table, if they do not exist (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "--schemachange-dry-run",
        action="store_const",
        const=True,
        default=None,
        dest="dry_run",
        help="Run schemachange in dry run mode (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "--schemachange-version-number-validation-regex",
        type=str,
        dest="version_number_validation_regex",
        help="If supplied, version numbers will be validated with this regular expression.",
        required=False,
    )
    parser_deploy.add_argument(
        "--schemachange-raise-exception-on-ignored-versioned-script",
        action="store_const",
        const=True,
        default=None,
        dest="raise_exception_on_ignored_versioned_script",
        help="Raise an exception if an un-applied versioned script is ignored (the default is False)",
        required=False,
    )

    # DEPRECATED: Old unprefixed arguments (kept for backward compatibility)
    parser_deploy.add_argument(
        "--change-history-table",
        type=str,
        dest="change_history_table",
        action="deprecate_schemachange",
        new_arg_short="-c",
        new_arg_long="--schemachange-change-history-table",
        help="Used to override the default name of the change history table (the default is "
        "METADATA.SCHEMACHANGE.CHANGE_HISTORY)",
        required=False,
    )
    parser_deploy.add_argument(
        "--autocommit",
        action="store_const",
        const=True,
        default=None,
        dest="autocommit",
        help="[DEPRECATED - Use -ac or --schemachange-autocommit instead.] Enable autocommit feature for DML commands (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "--query-tag",
        type=str,
        dest="query_tag",
        action="deprecate_schemachange",
        new_arg_short="-Q",
        new_arg_long="--schemachange-query-tag",
        help="The string to add to the Snowflake QUERY_TAG session value for each query executed",
        required=False,
    )
    parser_deploy.add_argument(
        "--connection-name",
        type=str,
        dest="connection_name",
        action="deprecate_schemachange",
        new_arg_short="-C",
        new_arg_long="--schemachange-connection-name",
        help="Override the default connections.toml connection name. Other connection-related values will override these connection values.",
        required=False,
    )
    parser_deploy.add_argument(
        "--connections-file-path",
        type=str,
        dest="connections_file_path",
        action="deprecate_schemachange",
        new_arg_long="--schemachange-connections-file-path",
        help="Override the default connections.toml file path at snowflake.connector.constants.CONNECTIONS_FILE (OS specific)",
        required=False,
    )
    parser_deploy.add_argument(
        "--create-change-history-table",
        action="store_const",
        const=True,
        default=None,
        dest="create_change_history_table",
        help="[DEPRECATED - Use --schemachange-create-change-history-table instead.] Create the change history schema and table, if they do not exist (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "--dry-run",
        action="store_const",
        const=True,
        default=None,
        dest="dry_run",
        help="[DEPRECATED - Use --schemachange-dry-run instead.] Run schemachange in dry run mode (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "--version-number-validation-regex",
        type=str,
        dest="version_number_validation_regex",
        action="deprecate_schemachange",
        new_arg_long="--schemachange-version-number-validation-regex",
        help="If supplied, version numbers will be validated with this regular expression.",
        required=False,
    )
    parser_deploy.add_argument(
        "--raise-exception-on-ignored-versioned-script",
        action="store_const",
        const=True,
        default=None,
        dest="raise_exception_on_ignored_versioned_script",
        help="[DEPRECATED - Use --schemachange-raise-exception-on-ignored-versioned-script instead.] Raise an exception if an un-applied versioned script is ignored (the default is False)",
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
    deprecate_log_level(args=args)
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
