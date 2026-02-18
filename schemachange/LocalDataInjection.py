from __future__ import annotations

import csv
import json
import os
import warnings
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
            raise ValueError(f"Could not find environmental variable {env_var} and no default value was provided")

        return result

    @staticmethod
    def from_csv(
        file_path: str,
        as_dict: bool = False,
        delimiter: str = ",",
        encoding: str = "utf-8",
        quotechar: str = '"',
        escapechar: str | None = None,
        doublequote: bool = True,
        skipinitialspace: bool = False,
        quoting: int = csv.QUOTE_MINIMAL,
        strict: bool = False,
        max_file_size: int | None = 50 * 1024 * 1024,
    ) -> list[tuple | dict[str, Any]]:
        """
        Loads data from a CSV file and returns it as a list of tuples or dictionaries.

        Args:
            file_path: Path to the CSV file
            as_dict: If True, returns list of dictionaries. If False, returns list of tuples
            delimiter: CSV delimiter character (must be a single character)
            encoding: File encoding
            quotechar: Character used to quote fields containing special characters
            escapechar: Character used to escape the delimiter if quoting is set to QUOTE_NONE
            doublequote: Controls how quotechar appearing inside a field should be quoted
            skipinitialspace: If True, whitespace immediately following the delimiter is ignored
            quoting: Controls when quotes should be recognized (csv.QUOTE_* constants)
            strict: If True, raise exception on bad CSV input
            max_file_size: Maximum file size in bytes (default 50MB). Set to None to disable size check.

        Returns:
            List of tuples or dictionaries representing CSV data
        """
        csv_path = Path(file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        # Check file size if max_file_size is set
        if max_file_size is not None:
            file_size = csv_path.stat().st_size
            if file_size > max_file_size:
                raise ValueError(f"CSV file exceeds {max_file_size / 1024 / 1024:.0f}MB limit: {file_path} ({file_size / 1024 / 1024:.2f}MB)")
        
        # Validate delimiter
        if not isinstance(delimiter, str) or len(delimiter) != 1:
            raise ValueError("Delimiter must be a single character")
        
        # Validate quotechar
        if not isinstance(quotechar, str) or len(quotechar) != 1:
            raise ValueError("Quotechar must be a single character")
        
        # Validate escapechar if provided
        if escapechar is not None and (not isinstance(escapechar, str) or len(escapechar) != 1):
            raise ValueError("Escapechar must be a single character or None")

        # Use CSV Sniffer to detect format and warn if parameters don't match
        with open(csv_path, encoding=encoding) as csvfile:
            # Read a sample for the sniffer
            sample = csvfile.read(8192)  # Read first 8KB for analysis
            csvfile.seek(0)  # Reset to beginning
            
            try:
                sniffer = csv.Sniffer()
                detected_dialect = sniffer.sniff(sample)
                
                # Warn if detected delimiter differs from provided delimiter
                if hasattr(detected_dialect, 'delimiter') and detected_dialect.delimiter != delimiter:
                    warnings.warn(
                        f"Detected delimiter '{detected_dialect.delimiter}' differs from "
                        f"provided delimiter '{delimiter}' in file {file_path}",
                        UserWarning,
                        stacklevel=2
                    )
                
                # Warn if detected quotechar differs from provided quotechar
                if hasattr(detected_dialect, 'quotechar') and detected_dialect.quotechar != quotechar:
                    warnings.warn(
                        f"Detected quotechar '{detected_dialect.quotechar}' differs from "
                        f"provided quotechar '{quotechar}' in file {file_path}",
                        UserWarning,
                        stacklevel=2
                    )
            except csv.Error:
                # Sniffer couldn't detect the format, continue with provided parameters
                pass

        # Build dialect parameters
        dialect_params = {
            "delimiter": delimiter,
            "quotechar": quotechar,
            "doublequote": doublequote,
            "skipinitialspace": skipinitialspace,
            "quoting": quoting,
            "strict": strict,
        }
        
        if escapechar is not None:
            dialect_params["escapechar"] = escapechar

        data = []

        with open(csv_path, encoding=encoding) as csvfile:
            if as_dict:
                reader = csv.DictReader(csvfile, **dialect_params)
                data = [dict(row) for row in reader]
            else:
                reader = csv.reader(csvfile, **dialect_params)
                data = [tuple(row) for row in reader]

        return data

    @staticmethod
    def from_json(
        file_path: str,
        encoding: str = "utf-8",
        max_file_size: int | None = 50 * 1024 * 1024,
    ) -> dict[str, Any] | list[Any]:
        """
        Loads data from a JSON file and returns it as a dictionary or list.

        Args:
            file_path: Path to the JSON file
            encoding: File encoding
            max_file_size: Maximum file size in bytes (default 50MB). Set to None to disable size check.

        Returns:
            Dictionary or list representing JSON data
        """
        json_path = Path(file_path)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        # Check file size if max_file_size is set
        if max_file_size is not None:
            file_size = json_path.stat().st_size
            if file_size > max_file_size:
                raise ValueError(f"JSON file exceeds {max_file_size / 1024 / 1024:.0f}MB limit: {file_path} ({file_size / 1024 / 1024:.2f}MB)")

        with open(json_path, encoding=encoding) as jsonfile:
            data = json.load(jsonfile)

        return data

    @staticmethod
    def from_yaml(
        file_path: str,
        encoding: str = "utf-8",
        max_file_size: int | None = 50 * 1024 * 1024,
    ) -> dict[str, Any] | list[Any]:
        """
        Loads data from a YAML file and returns it as a dictionary or list.

        Args:
            file_path: Path to the YAML file
            encoding: File encoding
            max_file_size: Maximum file size in bytes (default 50MB). Set to None to disable size check.

        Returns:
            Dictionary or list representing YAML data
        """
        yaml_path = Path(file_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        
        # Check file size if max_file_size is set
        if max_file_size is not None:
            file_size = yaml_path.stat().st_size
            if file_size > max_file_size:
                raise ValueError(f"YAML file exceeds {max_file_size / 1024 / 1024:.0f}MB limit: {file_path} ({file_size / 1024 / 1024:.2f}MB)")

        with open(yaml_path, encoding=encoding) as yamlfile:
            data = yaml.safe_load(yamlfile)

        return data
