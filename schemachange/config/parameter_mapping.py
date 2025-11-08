"""
Parameter Mapping Module

This module provides a centralized source of truth for all parameter names and mappings
across different configuration sources (CLI, ENV, YAML, connections.toml).

It ensures consistent parameter naming and conversion between different formats:
- CLI arguments: kebab-case (e.g., --root-folder)
- Environment variables: UPPER_SNAKE_CASE (e.g., SCHEMACHANGE_ROOT_FOLDER)
- Python parameters: snake_case (e.g., root_folder)
- YAML keys: kebab-case (e.g., root-folder)
"""

from enum import Enum
from typing import Any


class ParameterType(Enum):
    """Parameter data types for validation and conversion."""

    STRING = "string"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    JSON = "json"
    PATH = "path"
    LOG_LEVEL = "log_level"


class ParameterCategory(Enum):
    """Parameter categories for organization."""

    SCHEMACHANGE = "schemachange"
    SNOWFLAKE_CONNECTION = "snowflake_connection"
    SNOWFLAKE_AUTH = "snowflake_auth"
    SNOWFLAKE_ADDITIONAL = "snowflake_additional"


class Parameter:
    """
    Represents a configuration parameter with all its name variants and metadata.
    """

    def __init__(
        self,
        python_name: str,
        cli_long: str,
        env_var: str,
        param_type: ParameterType,
        category: ParameterCategory,
        cli_short: str | None = None,
        deprecated_cli_names: list[str] | None = None,
        description: str = "",
        default: Any = None,
    ):
        self.python_name = python_name  # snake_case for Python
        self.cli_long = cli_long  # kebab-case for CLI long form
        self.cli_short = cli_short  # single letter for CLI short form
        self.env_var = env_var  # UPPER_SNAKE_CASE for environment variables
        self.param_type = param_type
        self.category = category
        self.deprecated_cli_names = deprecated_cli_names or []
        self.description = description
        self.default = default

    @property
    def yaml_key(self) -> str:
        """YAML keys use kebab-case (same as CLI long form without prefix)."""
        # Remove --schemachange- or --snowflake- prefix
        if self.cli_long.startswith("--schemachange-"):
            return self.cli_long.replace("--schemachange-", "")
        elif self.cli_long.startswith("--snowflake-"):
            return self.cli_long.replace("--snowflake-", "")
        else:
            return self.cli_long.lstrip("-")

    def __repr__(self):
        return f"Parameter({self.python_name}, cli={self.cli_long}, env={self.env_var})"


# ============================================================================
# SCHEMACHANGE PARAMETERS
# ============================================================================

SCHEMACHANGE_PARAMETERS = [
    Parameter(
        python_name="root_folder",
        cli_long="--schemachange-root-folder",
        cli_short="-f",
        env_var="SCHEMACHANGE_ROOT_FOLDER",
        param_type=ParameterType.PATH,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--root-folder"],
        description="The root folder for database change scripts",
        default=".",
    ),
    Parameter(
        python_name="modules_folder",
        cli_long="--schemachange-modules-folder",
        cli_short="-m",
        env_var="SCHEMACHANGE_MODULES_FOLDER",
        param_type=ParameterType.PATH,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--modules-folder"],
        description="The modules folder for jinja macros and templates",
    ),
    Parameter(
        python_name="change_history_table",
        cli_long="--schemachange-change-history-table",
        cli_short="-c",
        env_var="SCHEMACHANGE_CHANGE_HISTORY_TABLE",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--change-history-table"],
        description="Override the default change history table name",
        default="METADATA.SCHEMACHANGE.CHANGE_HISTORY",
    ),
    Parameter(
        python_name="config_vars",
        cli_long="--schemachange-vars",
        cli_short="-V",
        env_var="SCHEMACHANGE_VARS",
        param_type=ParameterType.JSON,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--vars"],
        description="Define variables for scripts in JSON format",
        default={},
    ),
    Parameter(
        python_name="create_change_history_table",
        cli_long="--schemachange-create-change-history-table",
        env_var="SCHEMACHANGE_CREATE_CHANGE_HISTORY_TABLE",
        param_type=ParameterType.BOOLEAN,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--create-change-history-table"],
        description="Create the change history table if it doesn't exist",
        default=False,
    ),
    Parameter(
        python_name="autocommit",
        cli_long="--schemachange-autocommit",
        cli_short="-ac",
        env_var="SCHEMACHANGE_AUTOCOMMIT",
        param_type=ParameterType.BOOLEAN,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--autocommit"],
        description="Enable autocommit for DML commands",
        default=False,
    ),
    Parameter(
        python_name="dry_run",
        cli_long="--schemachange-dry-run",
        env_var="SCHEMACHANGE_DRY_RUN",
        param_type=ParameterType.BOOLEAN,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--dry-run"],
        description="Run in dry run mode",
        default=False,
    ),
    Parameter(
        python_name="query_tag",
        cli_long="--schemachange-query-tag",
        cli_short="-Q",
        env_var="SCHEMACHANGE_QUERY_TAG",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--query-tag"],
        description="String to include in QUERY_TAG attached to every SQL statement",
    ),
    Parameter(
        python_name="log_level",
        cli_long="--schemachange-log-level",
        cli_short="-L",
        env_var="SCHEMACHANGE_LOG_LEVEL",
        param_type=ParameterType.LOG_LEVEL,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--log-level"],
        description="Logging level: DEBUG, INFO, WARNING, ERROR, or CRITICAL",
        default="INFO",
    ),
    Parameter(
        python_name="connection_name",
        cli_long="--schemachange-connection-name",
        cli_short="-C",
        env_var="SCHEMACHANGE_CONNECTION_NAME",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--connection-name"],
        description="Override the default connections.toml connection profile name",
    ),
    Parameter(
        python_name="connections_file_path",
        cli_long="--schemachange-connections-file-path",
        env_var="SCHEMACHANGE_CONNECTIONS_FILE_PATH",
        param_type=ParameterType.PATH,
        category=ParameterCategory.SCHEMACHANGE,
        deprecated_cli_names=["--connections-file-path"],
        description="Override the default connections.toml file path",
    ),
    Parameter(
        python_name="version_number_validation_regex",
        cli_long="--schemachange-version-number-validation-regex",
        env_var="SCHEMACHANGE_VERSION_NUMBER_VALIDATION_REGEX",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SCHEMACHANGE,
        description="Regex pattern for version number validation",
    ),
    Parameter(
        python_name="raise_exception_on_ignored_versioned_script",
        cli_long="--schemachange-raise-exception-on-ignored-versioned-script",
        env_var="SCHEMACHANGE_RAISE_EXCEPTION_ON_IGNORED_VERSIONED_SCRIPT",
        param_type=ParameterType.BOOLEAN,
        category=ParameterCategory.SCHEMACHANGE,
        description="Raise exception when versioned scripts are ignored",
        default=False,
    ),
]

# ============================================================================
# SNOWFLAKE CONNECTION PARAMETERS
# ============================================================================

SNOWFLAKE_CONNECTION_PARAMETERS = [
    Parameter(
        python_name="snowflake_account",
        cli_long="--snowflake-account",
        cli_short="-a",
        env_var="SNOWFLAKE_ACCOUNT",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SNOWFLAKE_CONNECTION,
        description="Snowflake account identifier",
    ),
    Parameter(
        python_name="snowflake_user",
        cli_long="--snowflake-user",
        cli_short="-u",
        env_var="SNOWFLAKE_USER",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SNOWFLAKE_CONNECTION,
        description="Username for authentication",
    ),
    Parameter(
        python_name="snowflake_role",
        cli_long="--snowflake-role",
        cli_short="-r",
        env_var="SNOWFLAKE_ROLE",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SNOWFLAKE_CONNECTION,
        description="Role to use after connecting",
    ),
    Parameter(
        python_name="snowflake_warehouse",
        cli_long="--snowflake-warehouse",
        cli_short="-w",
        env_var="SNOWFLAKE_WAREHOUSE",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SNOWFLAKE_CONNECTION,
        description="Default warehouse",
    ),
    Parameter(
        python_name="snowflake_database",
        cli_long="--snowflake-database",
        cli_short="-d",
        env_var="SNOWFLAKE_DATABASE",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SNOWFLAKE_CONNECTION,
        description="Default database",
    ),
    Parameter(
        python_name="snowflake_schema",
        cli_long="--snowflake-schema",
        cli_short="-s",
        env_var="SNOWFLAKE_SCHEMA",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SNOWFLAKE_CONNECTION,
        description="Default schema",
    ),
]

# ============================================================================
# SNOWFLAKE AUTHENTICATION PARAMETERS
# ============================================================================

SNOWFLAKE_AUTH_PARAMETERS = [
    Parameter(
        python_name="authenticator",
        cli_long="--snowflake-authenticator",
        env_var="SNOWFLAKE_AUTHENTICATOR",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SNOWFLAKE_AUTH,
        description="Authentication method",
    ),
    Parameter(
        python_name="private_key_path",
        cli_long="--snowflake-private-key-path",
        env_var="SNOWFLAKE_PRIVATE_KEY_PATH",
        param_type=ParameterType.PATH,
        category=ParameterCategory.SNOWFLAKE_AUTH,
        description="Path to private key file for JWT authentication",
    ),
    Parameter(
        python_name="private_key_passphrase",
        cli_long="--snowflake-private-key-passphrase",
        env_var="SNOWFLAKE_PRIVATE_KEY_PASSPHRASE",
        param_type=ParameterType.STRING,
        category=ParameterCategory.SNOWFLAKE_AUTH,
        description="Passphrase for encrypted private key",
    ),
    Parameter(
        python_name="token_file_path",
        cli_long="--snowflake-token-file-path",
        env_var="SNOWFLAKE_TOKEN_FILE_PATH",
        param_type=ParameterType.PATH,
        category=ParameterCategory.SNOWFLAKE_AUTH,
        description="Path to OAuth token file",
    ),
]

# ============================================================================
# ALL PARAMETERS REGISTRY
# ============================================================================

ALL_PARAMETERS = SCHEMACHANGE_PARAMETERS + SNOWFLAKE_CONNECTION_PARAMETERS + SNOWFLAKE_AUTH_PARAMETERS

# ============================================================================
# LOOKUP DICTIONARIES FOR FAST ACCESS
# ============================================================================

# Map Python parameter names to Parameter objects
PYTHON_NAME_TO_PARAM = {param.python_name: param for param in ALL_PARAMETERS}

# Map CLI long forms to Parameter objects
CLI_LONG_TO_PARAM = {param.cli_long: param for param in ALL_PARAMETERS}

# Map CLI short forms to Parameter objects
CLI_SHORT_TO_PARAM = {param.cli_short: param for param in ALL_PARAMETERS if param.cli_short}

# Map environment variable names to Parameter objects
ENV_VAR_TO_PARAM = {param.env_var: param for param in ALL_PARAMETERS}

# Map deprecated CLI names to their new Parameter objects
DEPRECATED_CLI_TO_PARAM = {}
for param in ALL_PARAMETERS:
    for deprecated_name in param.deprecated_cli_names:
        DEPRECATED_CLI_TO_PARAM[deprecated_name] = param

# Map YAML keys to Parameter objects (for both schemachange and snowflake sections)
YAML_KEY_TO_PARAM = {param.yaml_key: param for param in ALL_PARAMETERS}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_parameter_by_python_name(python_name: str) -> Parameter | None:
    """Get Parameter object by Python parameter name."""
    return PYTHON_NAME_TO_PARAM.get(python_name)


def get_parameter_by_cli_arg(cli_arg: str) -> Parameter | None:
    """Get Parameter object by CLI argument (long or short form)."""
    # Try long form first
    param = CLI_LONG_TO_PARAM.get(cli_arg)
    if param:
        return param

    # Try short form
    param = CLI_SHORT_TO_PARAM.get(cli_arg)
    if param:
        return param

    # Try deprecated names
    return DEPRECATED_CLI_TO_PARAM.get(cli_arg)


def get_parameter_by_env_var(env_var: str) -> Parameter | None:
    """Get Parameter object by environment variable name."""
    return ENV_VAR_TO_PARAM.get(env_var)


def get_parameter_by_yaml_key(yaml_key: str) -> Parameter | None:
    """Get Parameter object by YAML key."""
    return YAML_KEY_TO_PARAM.get(yaml_key)


def is_deprecated_cli_arg(cli_arg: str) -> bool:
    """Check if a CLI argument is deprecated."""
    return cli_arg in DEPRECATED_CLI_TO_PARAM


def get_new_cli_arg_for_deprecated(deprecated_cli_arg: str) -> tuple[str, str | None]:
    """
    Get the new CLI argument for a deprecated one.

    Returns:
        Tuple of (long_form, short_form or None)
    """
    param = DEPRECATED_CLI_TO_PARAM.get(deprecated_cli_arg)
    if param:
        return param.cli_long, param.cli_short
    return deprecated_cli_arg, None


def convert_kebab_to_snake(kebab_str: str) -> str:
    """Convert kebab-case to snake_case."""
    return kebab_str.replace("-", "_")


def convert_snake_to_kebab(snake_str: str) -> str:
    """Convert snake_case to kebab-case."""
    return snake_str.replace("_", "-")


def convert_snake_to_upper_snake(snake_str: str) -> str:
    """Convert snake_case to UPPER_SNAKE_CASE."""
    return snake_str.upper()


def get_parameters_by_category(category: ParameterCategory) -> list[Parameter]:
    """Get all parameters in a specific category."""
    return [param for param in ALL_PARAMETERS if param.category == category]


def get_schemachange_env_var_names() -> list[str]:
    """Get all SCHEMACHANGE_* environment variable names."""
    return [param.env_var for param in ALL_PARAMETERS if param.category == ParameterCategory.SCHEMACHANGE]


def get_snowflake_env_var_names() -> list[str]:
    """Get all explicitly-handled SNOWFLAKE_* environment variable names."""
    return [
        param.env_var
        for param in ALL_PARAMETERS
        if param.category in (ParameterCategory.SNOWFLAKE_CONNECTION, ParameterCategory.SNOWFLAKE_AUTH)
    ]


# ============================================================================
# KNOWN SNOWFLAKE CONNECTOR BOOLEAN PARAMETERS
# ============================================================================
# These are used for type conversion in generic SNOWFLAKE_* env var pass-through

SNOWFLAKE_CONNECTOR_BOOLEAN_PARAMS = {
    "client_session_keep_alive",
    "validate_default_parameters",
    "ocsp_fail_open",
    "disable_request_pooling",
    "use_openssl_only",
    "client_store_temporary_credential",
    "support_negative_year",
    "arrow_number_to_decimal",
}

# ============================================================================
# KNOWN SNOWFLAKE CONNECTOR NUMERIC PARAMETERS
# ============================================================================

SNOWFLAKE_CONNECTOR_NUMERIC_PARAMS = {
    "login_timeout",
    "network_timeout",
    "socket_timeout",
    "client_prefetch_threads",
    "arrow_max_text_size",
}
