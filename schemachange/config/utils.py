from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


import jinja2
import jinja2.ext
import structlog
import yaml
from schemachange.JinjaEnvVar import JinjaEnvVar
import warnings

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
        raise ValueError(
            f"Invalid {input_type}: {input_value}. Missing ending double quote"
        )
    elif not input_value.startswith('"') and input_value.endswith('"'):
        raise ValueError(
            f"Invalid {input_type}: {input_value}. Missing beginning double quote"
        )
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
                extracted_secrets = (
                    extracted_secrets
                    | inner_extract_dictionary_secrets(value, child_of_secrets)
                )
            elif child_of_secrets or "SECRET" in key.upper():
                extracted_secrets.add(value.strip())

        return extracted_secrets

    return inner_extract_dictionary_secrets(config_vars)


def validate_file_path(file_path: Path | str | None) -> Path | None:
    if file_path is None:
        return None
    if isinstance(file_path, str):
        file_path = Path(file_path)
    if not file_path.is_file():
        raise ValueError(f"invalid file path: {str(file_path)}")
    return file_path


def validate_directory(path: Path | str | None) -> Path | None:
    if path is None:
        return None
    if isinstance(path, str):
        path = Path(path)
    if not path.is_dir():
        raise ValueError(f"Path is not valid directory: {str(path)}")
    return path


def validate_config_vars(config_vars: str | dict | None) -> dict:
    if config_vars is None:
        return {}

    if not isinstance(config_vars, dict):
        raise ValueError(
            f"config_vars did not parse correctly, please check its configuration: {config_vars}"
        )

    if "schemachange" in config_vars.keys():
        raise ValueError(
            "The variable 'schemachange' has been reserved for use by schemachange, please use a different name"
        )

    return config_vars


def load_yaml_config(config_file_path: Path | None) -> dict[str, Any]:
    """
    Loads the schemachange config file and processes with jinja templating engine
    """
    config = dict()

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

            # The FullLoader parameter handles the conversion from YAML scalar values to Python the dictionary format
            config = yaml.load(config_template.render(), Loader=yaml.FullLoader)
        logger.info("Using config file", config_file_path=str(config_file_path))
    return config


def get_snowsql_pwd() -> str | None:
    snowsql_pwd = os.getenv("SNOWSQL_PWD")
    if snowsql_pwd is not None and snowsql_pwd:
        warnings.warn(
            "The SNOWSQL_PWD environment variable is deprecated and "
            "will be removed in a later version of schemachange. "
            "Please use SNOWFLAKE_PASSWORD instead.",
            DeprecationWarning,
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
    Get Snowflake private key file path from environment variable.

    Returns:
        Private key file path from SNOWFLAKE_PRIVATE_KEY_PATH environment variable,
        or None if not set or empty.

    Used for JWT (snowflake_jwt) authentication.
    """
    private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
    if private_key_path is not None and private_key_path:
        return private_key_path
    return None


def get_snowflake_private_key_passphrase() -> str | None:
    """
    Get Snowflake private key passphrase from environment variable.

    Returns:
        Private key passphrase from SNOWFLAKE_PRIVATE_KEY_PASSPHRASE environment variable,
        or None if not set or empty.

    Used when the private key file is encrypted.
    """
    passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
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
