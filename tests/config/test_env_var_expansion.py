"""Tests for environment variable expansion in connections.toml."""

import os
from unittest import mock

from schemachange.config.utils import _expand_env_vars_in_dict, get_connections_toml_parameters


class TestExpandEnvVarsInDict:
    """Test environment variable expansion helper function."""

    def test_expand_simple_env_var(self):
        """Test $VAR syntax expansion."""
        with mock.patch.dict(os.environ, {"MY_PASSWORD": "secret123"}):
            params = {"password": "$MY_PASSWORD", "user": "testuser"}
            result = _expand_env_vars_in_dict(params)
            assert result["password"] == "secret123"
            assert result["user"] == "testuser"

    def test_expand_braced_env_var(self):
        """Test ${VAR} syntax expansion."""
        with mock.patch.dict(os.environ, {"SNOWFLAKE_ACCOUNT": "myaccount"}):
            params = {"account": "${SNOWFLAKE_ACCOUNT}", "user": "testuser"}
            result = _expand_env_vars_in_dict(params)
            assert result["account"] == "myaccount"
            assert result["user"] == "testuser"

    def test_expand_multiple_env_vars(self):
        """Test multiple environment variables in same dict."""
        with mock.patch.dict(os.environ, {"ACCOUNT": "myaccount", "PASSWORD": "mypass", "WAREHOUSE": "COMPUTE_WH"}):
            params = {
                "account": "$ACCOUNT",
                "password": "${PASSWORD}",
                "warehouse": "$WAREHOUSE",
                "user": "literal_user",
            }
            result = _expand_env_vars_in_dict(params)
            assert result["account"] == "myaccount"
            assert result["password"] == "mypass"
            assert result["warehouse"] == "COMPUTE_WH"
            assert result["user"] == "literal_user"

    def test_preserve_undefined_env_var(self):
        """Test that undefined env vars are preserved (not expanded)."""
        with mock.patch.dict(os.environ, {}, clear=True):
            params = {"password": "$UNDEFINED_VAR", "account": "${MISSING}"}
            result = _expand_env_vars_in_dict(params)
            # Snowflake connector preserves undefined vars
            assert result["password"] == "$UNDEFINED_VAR"
            assert result["account"] == "${MISSING}"

    def test_mixed_defined_and_undefined(self):
        """Test mix of defined and undefined variables."""
        with mock.patch.dict(os.environ, {"DEFINED": "value123"}):
            params = {"password": "$DEFINED", "account": "$UNDEFINED"}
            result = _expand_env_vars_in_dict(params)
            assert result["password"] == "value123"
            assert result["account"] == "$UNDEFINED"

    def test_non_string_values_passthrough(self):
        """Test that non-string values are not modified."""
        with mock.patch.dict(os.environ, {"PORT": "443"}):
            params = {
                "port": 443,  # integer
                "keep_alive": True,  # boolean
                "timeout": None,  # None
                "password": "$PORT",  # string
            }
            result = _expand_env_vars_in_dict(params)
            assert result["port"] == 443
            assert result["keep_alive"] is True
            assert result["timeout"] is None
            assert result["password"] == "443"

    def test_partial_env_var_in_string(self):
        """Test env var embedded in larger string."""
        with mock.patch.dict(os.environ, {"ENV": "prod"}):
            params = {"database": "mydb_$ENV", "schema": "${ENV}_schema"}
            result = _expand_env_vars_in_dict(params)
            assert result["database"] == "mydb_prod"
            assert result["schema"] == "prod_schema"

    def test_empty_dict(self):
        """Test empty dictionary."""
        result = _expand_env_vars_in_dict({})
        assert result == {}

    def test_special_characters_in_value(self):
        """Test that values with special characters work correctly."""
        with mock.patch.dict(os.environ, {"PASS": "p@ssw0rd!#$%"}):
            params = {"password": "$PASS"}
            result = _expand_env_vars_in_dict(params)
            assert result["password"] == "p@ssw0rd!#$%"


class TestConnectionsTomlEnvVarExpansion:
    """Test environment variable expansion when reading connections.toml."""

    def test_env_var_expansion_in_connections_toml(self, tmp_path):
        """Test that env vars are expanded when reading connections.toml."""
        # Create a connections.toml with env var references
        toml_content = """
[test_connection]
account = "${SNOWFLAKE_ACCOUNT}"
user = "$SNOWFLAKE_USER"
password = "$SNOWFLAKE_PASSWORD"
role = "MYROLE"
warehouse = "COMPUTE_WH"
"""
        toml_file = tmp_path / "connections.toml"
        toml_file.write_text(toml_content)

        # Set environment variables
        with mock.patch.dict(
            os.environ,
            {
                "SNOWFLAKE_ACCOUNT": "myaccount",
                "SNOWFLAKE_USER": "myuser",
                "SNOWFLAKE_PASSWORD": "secret123",
            },
        ):
            connection_params, session_params = get_connections_toml_parameters(toml_file, "test_connection")

            # Verify expansion worked
            assert connection_params["account"] == "myaccount"
            assert connection_params["user"] == "myuser"
            assert connection_params["password"] == "secret123"
            assert connection_params["role"] == "MYROLE"
            assert connection_params["warehouse"] == "COMPUTE_WH"

    def test_env_var_expansion_with_private_key(self, tmp_path):
        """Test env var expansion for private key authentication (Issue #388)."""
        # Create connections.toml matching Issue #388's configuration
        toml_content = """
[default]
account = "$SNOWFLAKE_ACCOUNT"
user = "$SNOWFLAKE_USERNAME"
authenticator = "SNOWFLAKE_JWT"
role = "$SNOWFLAKE_ROLE"
warehouse = "$SNOWFLAKE_WAREHOUSE"
database = "$SNOWFLAKE_DATABASE"
schema = "$SNOWFLAKE_SCHEMA"
private_key_file = "$SNOWFLAKE_KEY_PATH"
private_key_file_pwd = "$SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"
"""
        toml_file = tmp_path / "connections.toml"
        toml_file.write_text(toml_content)

        # Set environment variables (simulating Issue #388's setup)
        with mock.patch.dict(
            os.environ,
            {
                "SNOWFLAKE_ACCOUNT": "myaccount",
                "SNOWFLAKE_USERNAME": "myuser",
                "SNOWFLAKE_ROLE": "MYROLE",
                "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
                "SNOWFLAKE_DATABASE": "MYDB",
                "SNOWFLAKE_SCHEMA": "PUBLIC",
                "SNOWFLAKE_KEY_PATH": "/path/to/key.p8",
                "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": "my_secret_password",
            },
        ):
            connection_params, session_params = get_connections_toml_parameters(toml_file, "default")

            # Verify all parameters expanded correctly
            assert connection_params["account"] == "myaccount"
            assert connection_params["user"] == "myuser"
            assert connection_params["authenticator"] == "SNOWFLAKE_JWT"
            assert connection_params["role"] == "MYROLE"
            assert connection_params["warehouse"] == "COMPUTE_WH"
            assert connection_params["database"] == "MYDB"
            assert connection_params["schema"] == "PUBLIC"
            assert connection_params["private_key_file"] == "/path/to/key.p8"
            # This is the critical one for Issue #388
            assert connection_params["private_key_file_pwd"] == "my_secret_password"

    def test_session_params_env_var_expansion(self, tmp_path):
        """Test that session parameters also support env var expansion."""
        toml_content = """
[test_connection]
account = "myaccount"
user = "myuser"

[test_connection.parameters]
QUERY_TAG = "$MY_QUERY_TAG"
TIMEZONE = "${MY_TIMEZONE}"
"""
        toml_file = tmp_path / "connections.toml"
        toml_file.write_text(toml_content)

        with mock.patch.dict(os.environ, {"MY_QUERY_TAG": "my_app", "MY_TIMEZONE": "America/New_York"}):
            connection_params, session_params = get_connections_toml_parameters(toml_file, "test_connection")

            assert session_params["QUERY_TAG"] == "my_app"
            assert session_params["TIMEZONE"] == "America/New_York"

    def test_undefined_env_vars_preserved(self, tmp_path):
        """Test that undefined env vars are preserved in connections.toml."""
        toml_content = """
[test_connection]
account = "myaccount"
password = "$UNDEFINED_PASSWORD"
"""
        toml_file = tmp_path / "connections.toml"
        toml_file.write_text(toml_content)

        with mock.patch.dict(os.environ, {}, clear=True):
            connection_params, session_params = get_connections_toml_parameters(toml_file, "test_connection")

            # Undefined vars should be preserved (not expanded to empty string)
            assert connection_params["password"] == "$UNDEFINED_PASSWORD"
