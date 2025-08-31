from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

import jinja2.ext
import yaml


class LocalDataInjection(jinja2.ext.Extension):
    """
    Extends Jinja Templates with access to environmental variables and local data files
    """

    def __init__(self, environment: jinja2.Environment):
        super().__init__(environment)

        # add globals
        environment.globals["env_var"] = LocalDataInjection.env_var
        environment.globals["from_csv"] = LocalDataInjection.from_csv
        environment.globals["from_json"] = LocalDataInjection.from_json
        environment.globals["from_yaml"] = LocalDataInjection.from_yaml

    @staticmethod
    def env_var(env_var: str, default: str | None = None) -> str:
        """
        Returns the value of the environmental variable or the default.
        """
        result = default
        if env_var in os.environ:
            result = os.environ[env_var]

        if result is None:
            raise ValueError(
                f"Could not find environmental variable {env_var} and no default value was provided"
            )

        return result

    @staticmethod
    def from_csv(
        file_path: str,
        as_dict: bool = False,
        delimiter: str = ",",
        encoding: str = "utf-8",
    ) -> list[tuple | dict[str, Any]]:
        """
        Loads data from a CSV file and returns it as a list of tuples or dictionaries.

        Args:
            file_path: Path to the CSV file
            as_dict: If True, returns list of dictionaries. If False, returns list of tuples
            delimiter: CSV delimiter character
            encoding: File encoding

        Returns:
            List of tuples or dictionaries representing CSV data
        """
        csv_path = Path(file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        data = []

        with open(csv_path, encoding=encoding) as csvfile:
            if as_dict:
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                data = [dict(row) for row in reader]
            else:
                reader = csv.reader(csvfile, delimiter=delimiter)
                data = [tuple(row) for row in reader]

        return data

    @staticmethod
    def from_json(
        file_path: str, encoding: str = "utf-8"
    ) -> dict[str, Any] | list[Any]:
        """
        Loads data from a JSON file and returns it as a dictionary or list.

        Args:
            file_path: Path to the JSON file
            encoding: File encoding

        Returns:
            Dictionary or list representing JSON data
        """
        json_path = Path(file_path)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(json_path, encoding=encoding) as jsonfile:
            data = json.load(jsonfile)

        return data

    @staticmethod
    def from_yaml(
        file_path: str, encoding: str = "utf-8"
    ) -> dict[str, Any] | list[Any]:
        """
        Loads data from a YAML file and returns it as a dictionary or list.

        Args:
            file_path: Path to the YAML file
            encoding: File encoding

        Returns:
            Dictionary or list representing YAML data
        """
        yaml_path = Path(file_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")

        with open(yaml_path, encoding=encoding) as yamlfile:
            data = yaml.safe_load(yamlfile)

        return data
