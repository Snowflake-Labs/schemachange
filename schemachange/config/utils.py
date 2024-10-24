from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import json

import requests
import jinja2
import jinja2.ext
import structlog
import yaml
from snowflake.connector.config_manager import CONFIG_MANAGER
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


def set_connections_toml_path(connections_file_path: Path) -> None:
    # Change config file path and force update cache
    # noinspection PyProtectedMember
    for i, s in enumerate(CONFIG_MANAGER._slices):
        if s.section == "connections":
            # noinspection PyProtectedMember
            CONFIG_MANAGER._slices[i] = s._replace(path=connections_file_path)
            CONFIG_MANAGER.read_config()
            break


def get_connection_kwargs(
    connections_file_path: Path | None = None, connection_name: str | None = None
) -> dict:
    if connections_file_path is not None:
        connections_file_path = validate_file_path(file_path=connections_file_path)
        set_connections_toml_path(connections_file_path=connections_file_path)

    if connection_name is None:
        return {}

    connections = CONFIG_MANAGER["connections"]
    connection = connections.get(connection_name)
    if connection is None:
        raise Exception(
            f"Invalid connection_name '{connection_name}',"
            f" known ones are {list(connections.keys())}"
        )

    connection_kwargs = {
        "snowflake_account": connection.get("account"),
        "snowflake_user": connection.get("user"),
        "snowflake_role": connection.get("role"),
        "snowflake_warehouse": connection.get("warehouse"),
        "snowflake_database": connection.get("database"),
        "snowflake_schema": connection.get("schema"),
        "snowflake_authenticator": connection.get("authenticator"),
        "snowflake_password": connection.get("password"),
        "snowflake_private_key_path": connection.get("private-key"),
        "snowflake_token_path": connection.get("token-file-path"),
    }

    return {k: v for k, v in connection_kwargs.items() if v is not None}


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


def get_env_kwargs() -> dict[str, str]:
    env_kwargs = {
        "snowflake_password": get_snowflake_password(),
        "snowflake_private_key_path": os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"),
        "snowflake_authenticator": os.getenv("SNOWFLAKE_AUTHENTICATOR"),
        "snowflake_oauth_token": os.getenv("SNOWFLAKE_TOKEN"),
    }
    return {k: v for k, v in env_kwargs.items() if v is not None}


def get_oauth_token(oauth_config: dict):
    req_info = {
        "url": oauth_config["token-provider-url"],
        "headers": oauth_config["token-request-headers"],
        "data": oauth_config["token-request-payload"],
    }
    token_name = oauth_config["token-response-name"]
    response = requests.post(**req_info)
    response_dict = json.loads(response.text)
    try:
        return response_dict[token_name]
    except KeyError:
        keys = ", ".join(response_dict.keys())
        errormessage = f"Response Json contains keys: {keys} \n but not {token_name}"
        # if there is an error passed with the response include that
        if "error_description" in response_dict.keys():
            errormessage = f"{errormessage}\n error description: {response_dict['error_description']}"
        raise KeyError(errormessage)
