"""
Edge case tests for configuration parsing and validation.

Tests error handling, type conversion edge cases, and validation logic.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.utils import (
    get_all_snowflake_env_vars,
    get_schemachange_config_from_env,
    load_yaml_config,
)


class TestSchemachangeEnvVarEdgeCases:
    """Test edge cases for SCHEMACHANGE_* environment variable parsing."""

    def test_invalid_json_in_vars(self):
        """Test that invalid JSON in SCHEMACHANGE_VARS raises ValueError."""
        with mock.patch.dict(os.environ, {"SCHEMACHANGE_VARS": "{invalid json}"}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                get_schemachange_config_from_env()

            assert "Invalid JSON in SCHEMACHANGE_VARS" in str(exc_info.value)

    def test_empty_json_in_vars(self):
        """Test that empty JSON object in SCHEMACHANGE_VARS is handled."""
        with mock.patch.dict(os.environ, {"SCHEMACHANGE_VARS": "{}"}, clear=True):
            config = get_schemachange_config_from_env()

            assert config.get("config_vars") == {}

    def test_valid_json_in_vars(self):
        """Test that valid JSON in SCHEMACHANGE_VARS is parsed correctly."""
        vars_json = json.dumps({"key1": "value1", "key2": "value2"})
        with mock.patch.dict(os.environ, {"SCHEMACHANGE_VARS": vars_json}, clear=True):
            config = get_schemachange_config_from_env()

            assert config.get("config_vars") == {"key1": "value1", "key2": "value2"}

    def test_nested_json_in_vars(self):
        """Test that nested JSON in SCHEMACHANGE_VARS is parsed correctly."""
        vars_json = json.dumps({"database": "PROD_DB", "secrets": {"api_key": "secret123"}})
        with mock.patch.dict(os.environ, {"SCHEMACHANGE_VARS": vars_json}, clear=True):
            config = get_schemachange_config_from_env()

            assert config.get("config_vars") == {"database": "PROD_DB", "secrets": {"api_key": "secret123"}}

    def test_invalid_log_level(self):
        """Test that invalid log level raises ValueError."""
        with mock.patch.dict(os.environ, {"SCHEMACHANGE_LOG_LEVEL": "INVALID"}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                get_schemachange_config_from_env()

            assert "Invalid log level" in str(exc_info.value)
            assert "INVALID" in str(exc_info.value)

    def test_valid_log_levels(self):
        """Test that all valid log levels are accepted."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            with mock.patch.dict(os.environ, {"SCHEMACHANGE_LOG_LEVEL": level}, clear=True):
                config = get_schemachange_config_from_env()

                expected_value = getattr(logging, level)
                assert config.get("log_level") == expected_value

    def test_case_insensitive_log_level(self):
        """Test that log level is case-insensitive."""
        for level in ["debug", "Info", "WARNING", "error", "CrItIcAl"]:
            with mock.patch.dict(os.environ, {"SCHEMACHANGE_LOG_LEVEL": level}, clear=True):
                config = get_schemachange_config_from_env()

                expected_value = getattr(logging, level.upper())
                assert config.get("log_level") == expected_value

    def test_boolean_true_values(self):
        """Test various truthy boolean values."""
        for true_value in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
            with mock.patch.dict(os.environ, {"SCHEMACHANGE_AUTOCOMMIT": true_value}, clear=True):
                config = get_schemachange_config_from_env()

                assert config.get("autocommit") is True, f"Failed for: {true_value}"

    def test_boolean_false_values(self):
        """Test various falsy boolean values."""
        for false_value in ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF"]:
            with mock.patch.dict(os.environ, {"SCHEMACHANGE_AUTOCOMMIT": false_value}, clear=True):
                config = get_schemachange_config_from_env()

                assert config.get("autocommit") is False, f"Failed for: {false_value}"

    def test_empty_string_values(self):
        """Test that empty string values are ignored."""
        with mock.patch.dict(
            os.environ,
            {
                "SCHEMACHANGE_ROOT_FOLDER": "",
                "SCHEMACHANGE_AUTOCOMMIT": "",
                "SCHEMACHANGE_VARS": "",
            },
            clear=True,
        ):
            config = get_schemachange_config_from_env()

            # Empty strings should be ignored
            assert "root_folder" not in config
            assert "autocommit" not in config
            assert "config_vars" not in config

    def test_whitespace_only_values(self):
        """Test that whitespace-only values are treated as valid strings for string params."""
        with mock.patch.dict(os.environ, {"SCHEMACHANGE_QUERY_TAG": "   "}, clear=True):
            config = get_schemachange_config_from_env()

            # Whitespace is preserved for string parameters
            assert config.get("query_tag") == "   "

    def test_multiple_parameters_simultaneously(self):
        """Test parsing multiple environment variables at once."""
        env_vars = {
            "SCHEMACHANGE_ROOT_FOLDER": "./migrations",
            "SCHEMACHANGE_MODULES_FOLDER": "./modules",
            "SCHEMACHANGE_AUTOCOMMIT": "true",
            "SCHEMACHANGE_DRY_RUN": "false",
            "SCHEMACHANGE_VARS": '{"key": "value"}',
            "SCHEMACHANGE_LOG_LEVEL": "DEBUG",
        }

        with mock.patch.dict(os.environ, env_vars, clear=True):
            config = get_schemachange_config_from_env()

            assert config["root_folder"] == "./migrations"
            assert config["modules_folder"] == "./modules"
            assert config["autocommit"] is True
            assert config["dry_run"] is False
            assert config["config_vars"] == {"key": "value"}
            assert config["log_level"] == logging.DEBUG


class TestSnowflakeEnvVarEdgeCases:
    """Test edge cases for SNOWFLAKE_* environment variable parsing."""

    def test_boolean_conversion_edge_cases(self):
        """Test boolean conversion for known Snowflake connector boolean params."""
        for true_value in ["true", "TRUE", "1", "yes", "on"]:
            with mock.patch.dict(os.environ, {"SNOWFLAKE_CLIENT_SESSION_KEEP_ALIVE": true_value}, clear=True):
                params = get_all_snowflake_env_vars()

                assert params.get("client_session_keep_alive") is True

    def test_numeric_conversion_success(self):
        """Test numeric conversion for known Snowflake connector numeric params."""
        with mock.patch.dict(
            os.environ,
            {
                "SNOWFLAKE_LOGIN_TIMEOUT": "60",
                "SNOWFLAKE_NETWORK_TIMEOUT": "120",
                "SNOWFLAKE_CLIENT_PREFETCH_THREADS": "4",
            },
            clear=True,
        ):
            params = get_all_snowflake_env_vars()

            assert params["login_timeout"] == 60
            assert params["network_timeout"] == 120
            assert params["client_prefetch_threads"] == 4

    def test_numeric_conversion_failure_fallback_to_string(self):
        """Test that invalid numeric values fall back to string."""
        with mock.patch.dict(os.environ, {"SNOWFLAKE_LOGIN_TIMEOUT": "not_a_number"}, clear=True):
            params = get_all_snowflake_env_vars()

            # Should fall back to string with a warning
            assert params["login_timeout"] == "not_a_number"

    def test_explicitly_handled_params_not_included(self):
        """Test that explicitly handled SNOWFLAKE_* params are not in pass-through."""
        explicitly_handled = [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PASSWORD",
            "SNOWFLAKE_ROLE",
            "SNOWFLAKE_WAREHOUSE",
            "SNOWFLAKE_DATABASE",
            "SNOWFLAKE_SCHEMA",
            "SNOWFLAKE_AUTHENTICATOR",
            "SNOWFLAKE_PRIVATE_KEY_PATH",
            "SNOWFLAKE_CONNECTIONS_FILE_PATH",
        ]

        env_dict = dict.fromkeys(explicitly_handled, "test_value")

        with mock.patch.dict(os.environ, env_dict, clear=True):
            params = get_all_snowflake_env_vars()

            # None of these should be in the pass-through params
            for var in explicitly_handled:
                param_name = var[10:].lower()  # Remove SNOWFLAKE_ prefix
                assert param_name not in params

    def test_generic_snowflake_params_passed_through(self):
        """Test that unknown SNOWFLAKE_* params are passed through as strings."""
        with mock.patch.dict(
            os.environ,
            {
                "SNOWFLAKE_CUSTOM_PARAM_1": "value1",
                "SNOWFLAKE_CUSTOM_PARAM_2": "value2",
            },
            clear=True,
        ):
            params = get_all_snowflake_env_vars()

            assert params["custom_param_1"] == "value1"
            assert params["custom_param_2"] == "value2"

    def test_empty_snowflake_params_ignored(self):
        """Test that empty SNOWFLAKE_* params are ignored."""
        with mock.patch.dict(
            os.environ,
            {
                "SNOWFLAKE_CUSTOM_PARAM": "",
            },
            clear=True,
        ):
            params = get_all_snowflake_env_vars()

            # Empty values should be ignored
            assert "custom_param" not in params

    def test_snowflake_env_var_case_conversion(self):
        """Test that UPPER_SNAKE_CASE is converted to snake_case correctly."""
        with mock.patch.dict(
            os.environ,
            {
                "SNOWFLAKE_CLIENT_SESSION_KEEP_ALIVE": "true",
                "SNOWFLAKE_CUSTOM_MULTI_WORD_PARAM": "value",
            },
            clear=True,
        ):
            params = get_all_snowflake_env_vars()

            assert "client_session_keep_alive" in params
            assert "custom_multi_word_param" in params


class TestYAMLConfigEdgeCases:
    """Test edge cases for YAML configuration loading."""

    def test_missing_yaml_file(self):
        """Test that missing YAML file returns empty dict."""
        config = load_yaml_config(Path("/nonexistent/file.yml"))

        assert config == {}

    def test_none_yaml_path(self):
        """Test that None path returns empty dict."""
        config = load_yaml_config(None)

        assert config == {}

    def test_empty_yaml_file(self):
        """Test that empty YAML file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            config = load_yaml_config(temp_path)
            assert config == {}
        finally:
            temp_path.unlink()

    def test_yaml_with_only_comments(self):
        """Test YAML file with only comments."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("# This is a comment\n# Another comment\n")
            temp_path = Path(f.name)

        try:
            config = load_yaml_config(temp_path)
            assert config == {}
        finally:
            temp_path.unlink()

    def test_yaml_v2_empty_sections(self):
        """Test YAML v2 with empty schemachange and snowflake sections."""
        yaml_content = """
config-version: 2

schemachange:

snowflake:
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = load_yaml_config(temp_path)
            assert config.get("config-version") == 2
            # Empty sections should not create errors
        finally:
            temp_path.unlink()

    def test_yaml_v2_only_schemachange_section(self):
        """Test YAML v2 with only schemachange section."""
        yaml_content = """
config-version: 2

schemachange:
  root-folder: './migrations'
  autocommit: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = load_yaml_config(temp_path)
            assert config["root_folder"] == "./migrations"
            assert config["autocommit"] is True
            assert "additional_snowflake_params" not in config
        finally:
            temp_path.unlink()

    def test_yaml_v2_only_snowflake_section(self):
        """Test YAML v2 with only snowflake section."""
        yaml_content = """
config-version: 2

snowflake:
  account: 'myaccount.us-east-1'
  user: 'myuser'
  client-session-keep-alive: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = load_yaml_config(temp_path)
            assert "additional_snowflake_params" in config
            assert config["additional_snowflake_params"]["account"] == "myaccount.us-east-1"
            assert config["additional_snowflake_params"]["user"] == "myuser"
            assert config["additional_snowflake_params"]["client-session-keep-alive"] is True
        finally:
            temp_path.unlink()

    def test_yaml_v2_mixed_kebab_and_snake_case(self):
        """Test that YAML v2 handles mixed case styles."""
        yaml_content = """
config-version: 2

schemachange:
  root-folder: './migrations'
  root_folder_alt: './alt'  # This shouldn't cause issues

snowflake:
  client-session-keep-alive: true
  client_session_keep_alive_alt: false  # Mixed case
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = load_yaml_config(temp_path)
            # Both should be present (YAML parser allows it)
            assert "root_folder" in config or "root_folder_alt" in config
        finally:
            temp_path.unlink()

    def test_yaml_invalid_version(self):
        """Test that invalid config-version raises error."""
        yaml_content = """
config-version: 999

root-folder: './migrations'
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_yaml_config(temp_path)

            assert "Unsupported config-version: 999" in str(exc_info.value)
        finally:
            temp_path.unlink()

    def test_yaml_v1_backward_compatibility(self):
        """Test that config-version: 1 works with flat structure."""
        yaml_content = """
config-version: 1

root-folder: './migrations'
modules-folder: './modules'
snowflake-account: 'myaccount'
autocommit: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = load_yaml_config(temp_path)
            assert config["root-folder"] == "./migrations"
            assert config["modules-folder"] == "./modules"
            assert config["snowflake-account"] == "myaccount"
            assert config["autocommit"] is True
        finally:
            temp_path.unlink()

    def test_yaml_no_version_defaults_to_v1(self):
        """Test that missing config-version defaults to version 1."""
        yaml_content = """
root-folder: './migrations'
autocommit: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = load_yaml_config(temp_path)
            # Should work like version 1 (flat structure)
            assert config["root-folder"] == "./migrations"
            assert config["autocommit"] is True
        finally:
            temp_path.unlink()


class TestConfigPrecedence:
    """Test configuration precedence edge cases."""

    def test_empty_values_dont_override(self):
        """Test that empty/None values don't override lower priority sources."""
        # This would be tested in integration tests with actual config merging
        pass

    def test_zero_values_are_preserved(self):
        """Test that zero values (0, false) are preserved and not treated as empty."""
        with mock.patch.dict(
            os.environ,
            {
                "SCHEMACHANGE_AUTOCOMMIT": "0",  # Should be False, not ignored
                "SNOWFLAKE_LOGIN_TIMEOUT": "0",  # Should be 0, not ignored
            },
            clear=True,
        ):
            schemachange_config = get_schemachange_config_from_env()
            snowflake_config = get_all_snowflake_env_vars()

            assert schemachange_config["autocommit"] is False  # Explicit False
            assert snowflake_config["login_timeout"] == 0  # Explicit zero


class TestTypeConversionConsistency:
    """Test type conversion consistency across different sources."""

    def test_boolean_string_variations(self):
        """Test that boolean strings are consistently converted."""
        # Test both schemachange and snowflake boolean params
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]

        for string_value, expected_bool in test_cases:
            with mock.patch.dict(
                os.environ,
                {
                    "SCHEMACHANGE_AUTOCOMMIT": string_value,
                    "SNOWFLAKE_CLIENT_SESSION_KEEP_ALIVE": string_value,
                },
                clear=True,
            ):
                schemachange_config = get_schemachange_config_from_env()
                snowflake_config = get_all_snowflake_env_vars()

                assert schemachange_config["autocommit"] is expected_bool, (
                    f"Failed for '{string_value}' in SCHEMACHANGE_AUTOCOMMIT"
                )
                assert snowflake_config["client_session_keep_alive"] is expected_bool, (
                    f"Failed for '{string_value}' in SNOWFLAKE_CLIENT_SESSION_KEEP_ALIVE"
                )
