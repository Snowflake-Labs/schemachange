from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import jinja2
import jinja2.ext
import structlog
import yaml

from schemachange.JinjaEnvVar import JinjaEnvVar

logger = structlog.getLogger(__name__)

snowflake_identifier_pattern = re.compile(r"^[\w]+$")


def get_snowflake_identifier_string(input_value: str, input_type: str) -> str:
    # Words with alphanumeric characters and underscores only.
    result = ""

    if input_value is None:
        result = None
    elif snowflake_identifier_pattern.match(input_value):
        result = input_value
    elif input_value.startswith('"') and input_value.endswith('"'):
        result = input_value
    elif input_value.startswith('"') and not input_value.endswith('"'):
        raise ValueError(
            f"Invalid {input_type}: {input_value}. Missing ending double quote"
        )
    elif not input_value.startswith('"') and input_value.endswith('"'):
        raise ValueError(
            f"Invalid {input_type}: {input_value}. Missing beginning double quote"
        )
    else:
        result = f'"{input_value}"'

    return result


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


def validate_file_path(file_path: Path | str) -> Path:
    if isinstance(file_path, str):
        file_path = Path(file_path)
    if not file_path.is_file():
        raise ValueError(f"invalid file path: {str(file_path)}")
    return file_path


def validate_directory(path: Path | str | None) -> Path | None:
    if path is None:
        return path
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
