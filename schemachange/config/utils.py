from __future__ import annotations

import json
import logging
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Any

import jinja2
import jinja2.ext
import structlog
import yaml

# Python 3.11+ has tomllib built-in, older versions need tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore

from schemachange.JinjaEnvVar import JinjaEnvVar

logger = structlog.getLogger(__name__)

snowflake_identifier_pattern = re.compile(r"^[\w]+$")


def get_snowflake_identifier_string(input_value: str, input_type: str) -> str | None:
    # Words with alphanumeric characters and underscores only.
    if input_value is None:
        return None
    elif snowflake_identifier_pattern.match(input_value):
        return input_value
    elif input_value.startswith('"') and input_value.endswith('"'):
        return input_value
    elif input_value.startswith('"') and not input_value.endswith('"'):
        raise ValueError(f"Invalid {input_type}: {input_value}. Missing ending double quote")
    elif not input_value.startswith('"') and input_value.endswith('"'):
        raise ValueError(f"Invalid {input_type}: {input_value}. Missing beginning double quote")
    else:
        return f'"{input_value}"'


def get_config_secrets(config_vars: dict[str, dict | str] | None) -> set[str]:
    """Extracts all secret values from the vars attributes in config"""

    def inner_extract_dictionary_secrets(
        dictionary: dict[str, dict | str] | None,
        child_of_secrets: bool = False,
    ) -> set[str]:
        """Considers any key with the word secret in the name as a secret or
        all values as secrets if a child of a key named secrets.

        defined as an inner/ nested function to provide encapsulation
        """
        extracted_secrets: set[str] = set()

        if not dictionary:
            return extracted_secrets

        for key, value in dictionary.items():
            if isinstance(value, dict):
                if key == "secrets":
                    child_of_secrets = True
                extracted_secrets = extracted_secrets | inner_extract_dictionary_secrets(value, child_of_secrets)
            elif child_of_secrets or "SECRET" in key.upper():
                extracted_secrets.add(value.strip())

        return extracted_secrets

    return inner_extract_dictionary_secrets(config_vars)


def validate_file_path(file_path: Path | str | None) -> Path | None:
    if file_path is None:
        return None
    if isinstance(file_path, str):
        file_path = Path(file_path)
    # Expand ~ to user's home directory
    file_path = file_path.expanduser()
    if not file_path.is_file():
        raise ValueError(f"invalid file path: {str(file_path)}")
    return file_path


def validate_connections_file_permissions(file_path: Path) -> None:
    """
    Validate that connections.toml file has secure permissions.

    Warns if file is readable by group or others, as it may contain
    sensitive credentials.

    Args:
        file_path: Path to connections.toml file
    """
    import stat
    import warnings

    if file_path is None or not file_path.exists():
        return

    try:
        file_stat = file_path.stat()
        mode = file_stat.st_mode

        # Check if file is readable by group or others
        if mode & stat.S_IRGRP or mode & stat.S_IROTH:
            warnings.warn(
                f"\n"
                f"SECURITY WARNING: connections.toml file has insecure permissions!\n"
                f"  File: {file_path}\n"
                f"  Current permissions: {oct(stat.S_IMODE(mode))}\n"
                f"  Recommended: 0o600 (read/write for owner only)\n"
                f"\n"
                f"To fix, run:\n"
                f"  chmod 600 {file_path}\n"
                f"\n"
                f"This file may contain sensitive credentials and should only be\n"
                f"readable by the file owner.\n",
                UserWarning,
                stacklevel=3,
            )

        # Also check if writable by group or others (even worse)
        if mode & stat.S_IWGRP or mode & stat.S_IWOTH:
            warnings.warn(
                f"\n"
                f"CRITICAL SECURITY WARNING: connections.toml is writable by others!\n"
                f"  File: {file_path}\n"
                f"  Current permissions: {oct(stat.S_IMODE(mode))}\n"
                f"  This is a CRITICAL security issue!\n"
                f"\n"
                f"To fix immediately, run:\n"
                f"  chmod 600 {file_path}\n",
                UserWarning,
                stacklevel=3,
            )
    except (OSError, AttributeError):
        # If we can't check permissions (e.g., on Windows), silently pass
        pass


def validate_directory(path: Path | str | None) -> Path | None:
    if path is None:
        return None
    if isinstance(path, str):
        path = Path(path)
    # Expand ~ to user's home directory
    path = path.expanduser()
    if not path.is_dir():
        raise ValueError(f"Path is not valid directory: {str(path)}")
    return path


def validate_config_vars(config_vars: str | dict | None) -> dict:
    if config_vars is None:
        return {}

    if not isinstance(config_vars, dict):
        raise ValueError(f"config_vars did not parse correctly, please check its configuration: {config_vars}")

    if "schemachange" in config_vars.keys():
        raise ValueError(
            "The variable 'schemachange' has been reserved for use by schemachange, please use a different name"
        )

    return config_vars


def load_yaml_config(config_file_path: Path | None) -> dict[str, Any]:
    """
    Loads the schemachange config file and processes with jinja templating engine.

    Supports two config versions:
    - Version 1 (default): Flat structure with all parameters at root level
    - Version 2: Sectioned structure with 'schemachange' and 'snowflake' sections

    Returns a flattened dict with all parameters at root level for internal use,
    plus an 'additional_snowflake_params' key for pass-through parameters.
    """
    config = {}

    # First read in the yaml config file, if present
    if config_file_path is not None and config_file_path.is_file():
        with config_file_path.open() as config_file:
            # Run the config file through the jinja engine to give access to environmental variables
            # The config file does not have the same access to the jinja functionality that a script
            # has.
            config_template = jinja2.Template(
                config_file.read(),
                undefined=jinja2.StrictUndefined,
                extensions=[JinjaEnvVar],
            )

            # The SafeLoader parameter handles the conversion from YAML scalar values to Python the dictionary format
            # SafeLoader is used instead of FullLoader for security - prevents arbitrary code execution
            raw_config = yaml.load(config_template.render(), Loader=yaml.SafeLoader)

            if raw_config is None:
                raw_config = {}

            # Detect config version (default to 1 if not specified)
            config_version = raw_config.get("config-version", 1)

            # Normalize version to int (1.0, 1.1, 1.x all become 1; 2.0, 2.x all become 2)
            if config_version is not None:
                try:
                    # Convert to float first to handle string versions, then to int
                    config_version = int(float(config_version))
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid config-version: {config_version}. Must be a number (1 or 2).") from e
            else:
                config_version = 1

            if config_version == 2:
                # Version 2: Sectioned structure
                config = _parse_yaml_v2(raw_config)
                logger.info("Using config file (version 2)", config_file_path=str(config_file_path))
            elif config_version == 1:
                # Version 1: Flat structure (existing format)
                config = raw_config
                # Check for sensitive parameters in v1 YAML (security warning)
                _check_yaml_v1_for_sensitive_params(config)
                logger.info("Using config file (version 1)", config_file_path=str(config_file_path))
            else:
                raise ValueError(f"Unsupported config-version: {config_version}. Supported versions are 1 and 2.")
    elif config_file_path is not None:
        # Config file path was specified but file doesn't exist
        logger.info(
            f"Config file '{config_file_path}' not found. "
            f"Using configuration from CLI arguments, environment variables, and defaults. "
            f"Setting config_file_path={config_file_path}"
        )

    return config


def _check_yaml_v1_for_sensitive_params(config: dict) -> None:
    """
    Check YAML v1 config for sensitive parameters and warn if found.

    Args:
        config: Flat YAML v1 configuration dictionary
    """
    import warnings

    sensitive_params_v1 = {
        "snowflake-password": "SNOWFLAKE_PASSWORD environment variable or connections.toml",
        "snowflake-private-key-passphrase": "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE environment variable or connections.toml (deprecated: use SNOWFLAKE_PRIVATE_KEY_FILE_PWD)",
        "snowflake-private-key-file-pwd": "SNOWFLAKE_PRIVATE_KEY_FILE_PWD environment variable or connections.toml",
    }

    found_sensitive = []
    for param, recommendation in sensitive_params_v1.items():
        if param in config and config[param]:
            found_sensitive.append((param, recommendation))

    if found_sensitive:
        warning_msg = (
            "\n"
            "SECURITY WARNING: Sensitive credentials found in YAML configuration!\n"
            "\n"
            "The following sensitive parameters should NOT be stored in YAML files:\n"
        )
        for param, recommendation in found_sensitive:
            warning_msg += f"  - {param}: Use {recommendation} instead\n"
        warning_msg += (
            "\n"
            "YAML files are often committed to version control and should not\n"
            "contain passwords or other secrets. Use environment variables\n"
            "or connections.toml (with proper file permissions) instead.\n"
            "\n"
            "Consider migrating to config-version 2 for better organization.\n"
        )
        warnings.warn(warning_msg, UserWarning, stacklevel=5)


def _parse_yaml_v2(raw_config: dict) -> dict[str, Any]:
    """
    Parse YAML config version 2 with separate schemachange and snowflake sections.

    Returns a flattened dict with all schemachange parameters at root level,
    and snowflake parameters stored in 'additional_snowflake_params' for pass-through.

    Converts kebab-case keys to snake_case for schemachange parameters.
    """
    import warnings

    config = {}

    # Extract schemachange section
    schemachange_section = raw_config.get("schemachange", {})
    if schemachange_section:
        # Flatten schemachange parameters to root level
        # Convert kebab-case to snake_case for Python parameter names
        for key, value in schemachange_section.items():
            snake_case_key = key.replace("-", "_")
            config[snake_case_key] = value

    # Extract snowflake section
    snowflake_section = raw_config.get("snowflake", {})
    if snowflake_section:
        # Check for sensitive parameters in YAML (security warning)
        sensitive_params = {
            "password": "SNOWFLAKE_PASSWORD environment variable or connections.toml",
            "private-key-passphrase": "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE environment variable or connections.toml (deprecated: use SNOWFLAKE_PRIVATE_KEY_FILE_PWD)",
            "private-key-file-pwd": "SNOWFLAKE_PRIVATE_KEY_FILE_PWD environment variable or connections.toml",
            "token": "token-file-path with SNOWFLAKE_TOKEN_FILE_PATH or connections.toml",
        }

        found_sensitive = []
        for param, recommendation in sensitive_params.items():
            if param in snowflake_section and snowflake_section[param]:
                found_sensitive.append((param, recommendation))

        if found_sensitive:
            warning_msg = (
                "\n"
                "SECURITY WARNING: Sensitive credentials found in YAML configuration!\n"
                "\n"
                "The following sensitive parameters should NOT be stored in YAML files:\n"
            )
            for param, recommendation in found_sensitive:
                warning_msg += f"  - {param}: Use {recommendation} instead\n"
            warning_msg += (
                "\n"
                "YAML files are often committed to version control and should not\n"
                "contain passwords, tokens, or other secrets. Use environment variables\n"
                "or connections.toml (with proper file permissions) instead.\n"
            )
            warnings.warn(warning_msg, UserWarning, stacklevel=4)

        # Store snowflake parameters for pass-through to connector
        # These will be handled separately in get_merged_config
        # Keep kebab-case as-is since Snowflake connector might expect it
        config["additional_snowflake_params"] = snowflake_section

    # Keep config-version in the flattened config
    if "config-version" in raw_config:
        config["config-version"] = raw_config["config-version"]

    return config


def get_snowsql_pwd() -> str | None:
    snowsql_pwd = os.getenv("SNOWSQL_PWD")
    if snowsql_pwd is not None and snowsql_pwd:
        warnings.warn(
            "The SNOWSQL_PWD environment variable is deprecated and "
            "will be removed in a later version of schemachange. "
            "Please use SNOWFLAKE_PASSWORD instead.",
            DeprecationWarning,
            stacklevel=2,
        )
    return snowsql_pwd


def get_snowflake_password() -> str | None:
    snowflake_password = os.getenv("SNOWFLAKE_PASSWORD")
    snowsql_pwd = get_snowsql_pwd()

    if snowflake_password is not None and snowflake_password:
        # Check legacy/deprecated env variable
        if snowsql_pwd is not None and snowsql_pwd:
            warnings.warn(
                "Environment variables SNOWFLAKE_PASSWORD and SNOWSQL_PWD "
                "are both present, using SNOWFLAKE_PASSWORD",
                DeprecationWarning,
                stacklevel=2,
            )
        return snowflake_password
    elif snowsql_pwd is not None and snowsql_pwd:
        return snowsql_pwd
    else:
        return None


def get_snowflake_account() -> str | None:
    """
    Get Snowflake account from environment variable.

    Returns:
        Account identifier from SNOWFLAKE_ACCOUNT environment variable,
        or None if not set or empty.
    """
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    if account is not None and account:
        return account
    return None


def get_snowflake_user() -> str | None:
    """
    Get Snowflake user from environment variable.

    Returns:
        User name from SNOWFLAKE_USER environment variable,
        or None if not set or empty.
    """
    user = os.getenv("SNOWFLAKE_USER")
    if user is not None and user:
        return user
    return None


def get_snowflake_role() -> str | None:
    """
    Get Snowflake role from environment variable.

    Returns:
        Role name from SNOWFLAKE_ROLE environment variable,
        or None if not set or empty.
    """
    role = os.getenv("SNOWFLAKE_ROLE")
    if role is not None and role:
        return role
    return None


def get_snowflake_warehouse() -> str | None:
    """
    Get Snowflake warehouse from environment variable.

    Returns:
        Warehouse name from SNOWFLAKE_WAREHOUSE environment variable,
        or None if not set or empty.
    """
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    if warehouse is not None and warehouse:
        return warehouse
    return None


def get_snowflake_database() -> str | None:
    """
    Get Snowflake database from environment variable.

    Returns:
        Database name from SNOWFLAKE_DATABASE environment variable,
        or None if not set or empty.
    """
    database = os.getenv("SNOWFLAKE_DATABASE")
    if database is not None and database:
        return database
    return None


def get_snowflake_schema() -> str | None:
    """
    Get Snowflake schema from environment variable.

    Returns:
        Schema name from SNOWFLAKE_SCHEMA environment variable,
        or None if not set or empty.
    """
    schema = os.getenv("SNOWFLAKE_SCHEMA")
    if schema is not None and schema:
        return schema
    return None


def get_snowflake_authenticator() -> str | None:
    """
    Get Snowflake authenticator from environment variable.

    Returns:
        Authenticator type from SNOWFLAKE_AUTHENTICATOR environment variable,
        or None if not set or empty.

    Valid values: 'snowflake', 'oauth', 'externalbrowser',
                  'https://<okta_account>.okta.com', 'snowflake_jwt'
    """
    authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR")
    if authenticator is not None and authenticator:
        return authenticator
    return None


def get_snowflake_private_key_path() -> str | None:
    """
    Get Snowflake private key file path from environment variable (deprecated).

    Returns:
        Private key file path from SNOWFLAKE_PRIVATE_KEY_PATH environment variable,
        or None if not set or empty.

    Used for JWT (snowflake_jwt) authentication.

    NOTE: DEPRECATED - Use get_snowflake_private_key_file() instead.
    This function is maintained for backward compatibility.
    """
    private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
    if private_key_path is not None and private_key_path:
        return private_key_path
    return None


def get_snowflake_private_key_file() -> str | None:
    """
    Get Snowflake private key file path from environment variable.

    Returns:
        Private key file path from SNOWFLAKE_PRIVATE_KEY_FILE environment variable,
        or None if not set or empty.

    Used for JWT (snowflake_jwt) authentication.
    This is the recommended parameter name (matches Snowflake Python Connector).
    """
    private_key_file = os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE")
    if private_key_file is not None and private_key_file:
        return private_key_file
    return None


def get_snowflake_private_key_passphrase() -> str | None:
    """
    Get Snowflake private key passphrase from environment variable (deprecated).

    Returns:
        Private key passphrase from SNOWFLAKE_PRIVATE_KEY_PASSPHRASE environment variable,
        or None if not set or empty.

    Used when the private key file is encrypted.

    NOTE: DEPRECATED - Use get_snowflake_private_key_file_pwd() instead.
    This function is maintained for backward compatibility.
    """
    passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
    if passphrase is not None and passphrase:
        return passphrase
    return None


def get_snowflake_private_key_file_pwd() -> str | None:
    """
    Get Snowflake private key passphrase from environment variable.

    Returns:
        Private key passphrase from SNOWFLAKE_PRIVATE_KEY_FILE_PWD environment variable,
        or None if not set or empty.

    Used for decrypting encrypted private keys in JWT authentication.
    This is the recommended parameter name (matches Snowflake Python Connector).
    """
    passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD")
    if passphrase is not None and passphrase:
        return passphrase
    return None


def get_snowflake_token_file_path() -> str | None:
    """
    Get Snowflake OAuth token file path from environment variable.

    Returns:
        Token file path from SNOWFLAKE_TOKEN_FILE_PATH environment variable,
        or None if not set or empty.

    Used for OAuth authentication.
    """
    token_file_path = os.getenv("SNOWFLAKE_TOKEN_FILE_PATH")
    if token_file_path is not None and token_file_path:
        return token_file_path
    return None


def get_snowflake_connections_file_path() -> str | None:
    """
    Get Snowflake connections.toml file path from environment variable.

    Returns:
        Connections file path from SNOWFLAKE_CONNECTIONS_FILE_PATH environment variable,
        or None if not set or empty.

    Used to override the default connections.toml location.
    """
    connections_file_path = os.getenv("SNOWFLAKE_CONNECTIONS_FILE_PATH")
    if connections_file_path is not None and connections_file_path:
        return connections_file_path
    return None


def get_snowflake_home() -> str:
    """
    Get Snowflake home directory from environment variable or user's home directory.

    Returns:
        Home directory from SNOWFLAKE_HOME environment variable if set,
        otherwise defaults to the current user's home directory.

    Used to locate the connections.toml file (default: ~/.snowflake).

    Raises:
        RuntimeError: If home directory cannot be determined from environment variables.
    """
    home = os.getenv("SNOWFLAKE_HOME")
    if home is not None and home:
        return home
    # Default to user's home directory
    # Path.home() can raise RuntimeError if it cannot determine the home directory
    # (e.g., on Windows when USERPROFILE is not set, or Unix when HOME is not set)
    try:
        return str(Path.home())
    except RuntimeError as e:
        raise RuntimeError(
            "Could not determine home directory. Please set SNOWFLAKE_HOME environment variable, "
            "or ensure HOME (Unix) or USERPROFILE (Windows) environment variables are set."
        ) from e


def get_snowflake_default_connection_name() -> str | None:
    """
    Get default Snowflake connection name from environment variable.

    Returns:
        Connection name from SNOWFLAKE_DEFAULT_CONNECTION_NAME environment variable,
        or None if not set or empty.

    Used to select which connection profile to use from connections.toml.
    """
    connection_name = os.getenv("SNOWFLAKE_DEFAULT_CONNECTION_NAME")
    if connection_name is not None and connection_name:
        return connection_name
    return None


def get_snowflake_session_parameters() -> dict | None:
    """
    Get Snowflake session parameters from environment variable.

    Returns:
        Session parameters dict from SNOWFLAKE_SESSION_PARAMETERS environment variable (JSON format),
        or None if not set or empty.

    Example:
        SNOWFLAKE_SESSION_PARAMETERS='{"QUOTED_IDENTIFIERS_IGNORE_CASE": false}'
    """
    session_params_str = os.getenv("SNOWFLAKE_SESSION_PARAMETERS")
    if session_params_str:
        try:
            return json.loads(session_params_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in SNOWFLAKE_SESSION_PARAMETERS environment variable: {e}") from e
    return None


def get_connections_toml_parameters(
    connections_file_path: Path | str | None, connection_name: str | None
) -> tuple[dict, dict]:
    """
    Read ALL connection parameters from connections.toml file for a specific connection.

    Returns both connection parameters and session parameters separately.

    Note: Connection parameters are returned WITHOUT the "snowflake_" prefix (e.g., "account", "user", "role").
    The caller is responsible for adding the prefix when merging with config objects that expect
    "snowflake_account", "snowflake_user", etc.

    Args:
        connections_file_path: Path to connections.toml file (defaults to ~/.snowflake/connections.toml if None)
        connection_name: Name of the connection profile to read

    Returns:
        Tuple of (connection_params, session_params) dictionaries
        - connection_params: Keys like "account", "user", "role" (snake_case, no "snowflake_" prefix)
        - session_params: Keys like "QUERY_TAG", "QUOTED_IDENTIFIERS_IGNORE_CASE" (UPPER_CASE)

    Example connections.toml:
        [production]
        account = "myaccount"
        user = "myuser"
        password = "mypassword"
        role = "MYROLE"
        warehouse = "MYWH"
        database = "MYDB"
        schema = "MYSCHEMA"

        [production.parameters]
        QUERY_TAG = "my_app"
        QUOTED_IDENTIFIERS_IGNORE_CASE = false
    """
    if not connection_name:
        return {}, {}

    # Default to ~/.snowflake/connections.toml if path not specified (matches Snowflake connector behavior)
    if not connections_file_path:
        snowflake_home = get_snowflake_home()
        connections_file_path = Path(snowflake_home) / ".snowflake" / "connections.toml"
        logger.debug(
            "Using default connections.toml path",
            path=str(connections_file_path),
            connection_name=connection_name,
        )

    if tomllib is None:
        logger.warning(
            "tomli/tomllib not available - cannot read parameters from connections.toml. "
            "Install tomli for Python < 3.11"
        )
        return {}, {}

    try:
        connections_file_path = Path(connections_file_path)

        # Expand ~ in path
        connections_file_path = connections_file_path.expanduser()

        logger.debug(
            "Attempting to read from connections.toml",
            file_path=str(connections_file_path),
            connection_name=connection_name,
            file_exists=connections_file_path.exists(),
        )

        if not connections_file_path.exists():
            logger.debug(
                f"connections.toml file not found at: {connections_file_path}",
                connection_name=connection_name,
            )
            return {}, {}

        with open(connections_file_path, "rb") as f:
            toml_data = tomllib.load(f)

        # Check if connection exists
        logger.debug(
            f"connections.toml loaded, available connections: {list(toml_data.keys())}",
            looking_for=connection_name,
        )

        if connection_name not in toml_data:
            logger.debug(
                f"Connection '{connection_name}' not found in connections.toml",
                available_connections=list(toml_data.keys()),
            )
            return {}, {}

        # Check if connection has parameters section
        connection_data = toml_data[connection_name]
        if not isinstance(connection_data, dict):
            return {}, {}

        # Extract connection parameters (excluding 'parameters' subsection)
        connection_params = {}
        for key, value in connection_data.items():
            if key != "parameters" and not isinstance(value, dict):
                # Convert kebab-case to snake_case for consistency with connector
                snake_key = key.replace("-", "_")
                connection_params[snake_key] = value

        # Get session parameters from [connection_name.parameters] section
        session_params = connection_data.get("parameters", {})
        if not isinstance(session_params, dict):
            session_params = {}

        logger.debug(
            f"Successfully read connection '{connection_name}' from connections.toml",
            connection_params_keys=list(connection_params.keys()),
            session_params_keys=list(session_params.keys()),
        )

        return connection_params, session_params

    except Exception as e:
        logger.warning(
            f"Failed to read parameters from connections.toml: {e}",
            connections_file=str(connections_file_path),
            connection_name=connection_name,
        )
        return {}, {}


def get_connections_toml_session_parameters(
    connections_file_path: Path | str | None, connection_name: str | None
) -> dict:
    """
    Read session parameters from connections.toml file for a specific connection.

    This is a convenience wrapper around get_connections_toml_parameters() that only returns session parameters.

    Args:
        connections_file_path: Path to connections.toml file (defaults to ~/.snowflake/connections.toml if None)
        connection_name: Name of the connection profile to read

    Returns:
        Dictionary of session parameters explicitly set in connections.toml
    """
    _, session_params = get_connections_toml_parameters(connections_file_path, connection_name)
    return session_params


def get_schemachange_config_from_env() -> dict:
    """
    Get schemachange-specific configuration from SCHEMACHANGE_* environment variables.

    Supports all schemachange parameters with proper type conversion:
    - Boolean parameters: accept true/false, 1/0, yes/no, on/off (case-insensitive)
    - JSON parameters: parse SCHEMACHANGE_VARS as JSON object
    - Log level: convert string (DEBUG/INFO/WARNING/ERROR/CRITICAL) to logging level int

    Returns:
        Dictionary with schemachange configuration parameters from environment
    """
    import json

    env_config = {}

    # String parameters
    string_params = {
        "SCHEMACHANGE_ROOT_FOLDER": "root_folder",
        "SCHEMACHANGE_MODULES_FOLDER": "modules_folder",
        "SCHEMACHANGE_CHANGE_HISTORY_TABLE": "change_history_table",
        "SCHEMACHANGE_QUERY_TAG": "query_tag",
        "SCHEMACHANGE_CONFIG_FOLDER": "config_folder",
        "SCHEMACHANGE_CONFIG_FILE_NAME": "config_file_name",
        "SCHEMACHANGE_CONNECTIONS_FILE_PATH": "connections_file_path",
        "SCHEMACHANGE_CONNECTION_NAME": "connection_name",
        "SCHEMACHANGE_VERSION_NUMBER_VALIDATION_REGEX": "version_number_validation_regex",
    }

    for env_var, param_name in string_params.items():
        value = os.getenv(env_var)
        if value:
            env_config[param_name] = value

    # Also support legacy SNOWFLAKE_* env vars for connections configuration
    # SCHEMACHANGE_* takes precedence if both are set
    if "connections_file_path" not in env_config:
        snowflake_conn_path = os.getenv("SNOWFLAKE_CONNECTIONS_FILE_PATH")
        if snowflake_conn_path:
            env_config["connections_file_path"] = snowflake_conn_path

    if "connection_name" not in env_config:
        snowflake_conn_name = os.getenv("SNOWFLAKE_DEFAULT_CONNECTION_NAME")
        if snowflake_conn_name:
            env_config["connection_name"] = snowflake_conn_name

    # Boolean parameters
    bool_params = {
        "SCHEMACHANGE_CREATE_CHANGE_HISTORY_TABLE": "create_change_history_table",
        "SCHEMACHANGE_INITIAL_DEPLOYMENT": "initial_deployment",
        "SCHEMACHANGE_AUTOCOMMIT": "autocommit",
        "SCHEMACHANGE_DRY_RUN": "dry_run",
        "SCHEMACHANGE_RAISE_EXCEPTION_ON_IGNORED_VERSIONED_SCRIPT": "raise_exception_on_ignored_versioned_script",
    }

    for env_var, param_name in bool_params.items():
        value = os.getenv(env_var)
        if value:
            # Convert string to boolean
            env_config[param_name] = value.lower() in ("true", "1", "yes", "on")

    # JSON parameter (vars)
    vars_value = os.getenv("SCHEMACHANGE_VARS")
    if vars_value:
        try:
            env_config["config_vars"] = json.loads(vars_value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in SCHEMACHANGE_VARS environment variable: {e}") from e

    # Log level parameter (string to int conversion)
    log_level_value = os.getenv("SCHEMACHANGE_LOG_LEVEL")
    if log_level_value:
        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        log_level_upper = log_level_value.upper()
        if log_level_upper in log_level_map:
            env_config["log_level"] = log_level_map[log_level_upper]
        else:
            raise ValueError(
                f"Invalid log level in SCHEMACHANGE_LOG_LEVEL: {log_level_value}. "
                f"Valid values are: DEBUG, INFO, WARNING, ERROR, CRITICAL"
            )

    return env_config


def get_all_snowflake_env_vars() -> dict:
    """
    Get all SNOWFLAKE_* environment variables for pass-through to Snowflake connector.

    Detects any SNOWFLAKE_* environment variable not explicitly handled elsewhere
    and prepares them for pass-through to snowflake.connector.connect().

    Applies type conversion for known boolean and numeric parameters.

    Returns:
        Dictionary with Snowflake connector parameters (snake_case keys)
    """
    snowflake_params = {}

    # Parameters already explicitly handled (skip these)
    explicitly_handled = {
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_ROLE",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
        "SNOWFLAKE_SCHEMA",
        "SNOWFLAKE_AUTHENTICATOR",
        "SNOWFLAKE_PRIVATE_KEY_PATH",
        "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE",
        "SNOWFLAKE_TOKEN_FILE_PATH",
        "SNOWFLAKE_CONNECTIONS_FILE_PATH",
        "SNOWFLAKE_DEFAULT_CONNECTION_NAME",
        "SNOWFLAKE_HOME",
        "SNOWFLAKE_SESSION_PARAMETERS",  # Handled separately as JSON
        "SNOWSQL_PWD",
    }

    # Known boolean parameters
    boolean_params = {
        "client_session_keep_alive",
        "validate_default_parameters",
        "disable_request_pooling",
        "ocsp_fail_open",
    }

    # Known numeric parameters
    numeric_params = {"login_timeout", "network_timeout", "socket_timeout", "client_prefetch_threads"}

    for env_var, value in os.environ.items():
        if env_var.startswith("SNOWFLAKE_") and value and env_var not in explicitly_handled:
            # Convert SNOWFLAKE_PARAM_NAME to param_name
            param_name = env_var[10:].lower()  # Remove 'SNOWFLAKE_' prefix

            # Apply type conversion
            if param_name in boolean_params:
                snowflake_params[param_name] = value.lower() in ("true", "1", "yes", "on")
            elif param_name in numeric_params:
                try:
                    snowflake_params[param_name] = int(value)
                except ValueError:
                    logger.warning(f"Invalid numeric value for {env_var}: {value}. Using as string.")
                    snowflake_params[param_name] = value
            else:
                # Pass through as string
                snowflake_params[param_name] = value

    return snowflake_params
