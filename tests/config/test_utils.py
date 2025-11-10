from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.utils import (
    _parse_yaml_v2,
    get_connections_toml_session_parameters,
    get_snowflake_account,
    get_snowflake_authenticator,
    get_snowflake_connections_file_path,
    get_snowflake_database,
    get_snowflake_default_connection_name,
    get_snowflake_home,
    get_snowflake_password,
    get_snowflake_private_key_passphrase,
    get_snowflake_private_key_path,
    get_snowflake_role,
    get_snowflake_schema,
    get_snowflake_token_file_path,
    get_snowflake_user,
    get_snowflake_warehouse,
    load_yaml_config,
    validate_file_path,
)

assets_path = Path(__file__).parent


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_PASSWORD": "my-password"}, "my-password"),
        ({"SNOWFLAKE_PASSWORD": ""}, None),
        ({}, None),
        ({"SNOWSQL_PWD": "my-password"}, "my-password"),
        (
            {"SNOWSQL_PWD": "my-password", "SNOWFLAKE_PASSWORD": "my-password"},
            "my-password",
        ),
    ],
)
def test_get_snowflake_password(env_vars: dict, expected: str):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_password()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_ACCOUNT": "my-account"}, "my-account"),
        ({"SNOWFLAKE_ACCOUNT": "xy12345.us-east-1"}, "xy12345.us-east-1"),
        ({"SNOWFLAKE_ACCOUNT": "org-accountname"}, "org-accountname"),
        ({"SNOWFLAKE_ACCOUNT": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_account(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_account()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_USER": "my-user"}, "my-user"),
        ({"SNOWFLAKE_USER": "john.doe@example.com"}, "john.doe@example.com"),
        ({"SNOWFLAKE_USER": "SERVICE_ACCOUNT_USER"}, "SERVICE_ACCOUNT_USER"),
        ({"SNOWFLAKE_USER": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_user(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_user()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_ROLE": "my-role"}, "my-role"),
        ({"SNOWFLAKE_ROLE": "ACCOUNTADMIN"}, "ACCOUNTADMIN"),
        ({"SNOWFLAKE_ROLE": "SYSADMIN"}, "SYSADMIN"),
        ({"SNOWFLAKE_ROLE": "DEVELOPER_ROLE"}, "DEVELOPER_ROLE"),
        ({"SNOWFLAKE_ROLE": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_role(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_role()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_WAREHOUSE": "my-warehouse"}, "my-warehouse"),
        ({"SNOWFLAKE_WAREHOUSE": "COMPUTE_WH"}, "COMPUTE_WH"),
        ({"SNOWFLAKE_WAREHOUSE": "DEV_WH"}, "DEV_WH"),
        ({"SNOWFLAKE_WAREHOUSE": "PROD_WAREHOUSE"}, "PROD_WAREHOUSE"),
        ({"SNOWFLAKE_WAREHOUSE": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_warehouse(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_warehouse()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_DATABASE": "my-database"}, "my-database"),
        ({"SNOWFLAKE_DATABASE": "PROD_DB"}, "PROD_DB"),
        ({"SNOWFLAKE_DATABASE": "DEV_DATABASE"}, "DEV_DATABASE"),
        ({"SNOWFLAKE_DATABASE": "ANALYTICS"}, "ANALYTICS"),
        ({"SNOWFLAKE_DATABASE": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_database(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_database()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_SCHEMA": "my-schema"}, "my-schema"),
        ({"SNOWFLAKE_SCHEMA": "PUBLIC"}, "PUBLIC"),
        ({"SNOWFLAKE_SCHEMA": "DEV_SCHEMA"}, "DEV_SCHEMA"),
        ({"SNOWFLAKE_SCHEMA": "STAGING"}, "STAGING"),
        ({"SNOWFLAKE_SCHEMA": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_schema(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_schema()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_AUTHENTICATOR": "snowflake"}, "snowflake"),
        ({"SNOWFLAKE_AUTHENTICATOR": "oauth"}, "oauth"),
        ({"SNOWFLAKE_AUTHENTICATOR": "externalbrowser"}, "externalbrowser"),
        ({"SNOWFLAKE_AUTHENTICATOR": "snowflake_jwt"}, "snowflake_jwt"),
        (
            {"SNOWFLAKE_AUTHENTICATOR": "https://mycompany.okta.com"},
            "https://mycompany.okta.com",
        ),
        ({"SNOWFLAKE_AUTHENTICATOR": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_authenticator(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_authenticator()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_PRIVATE_KEY_PATH": "/path/to/key.pem"}, "/path/to/key.pem"),
        (
            {"SNOWFLAKE_PRIVATE_KEY_PATH": "/home/user/.ssh/snowflake_key.p8"},
            "/home/user/.ssh/snowflake_key.p8",
        ),
        ({"SNOWFLAKE_PRIVATE_KEY_PATH": "~/keys/rsa_key.pem"}, "~/keys/rsa_key.pem"),
        ({"SNOWFLAKE_PRIVATE_KEY_PATH": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_private_key_path(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_private_key_path()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        (
            {"SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": "my-secret-passphrase"},
            "my-secret-passphrase",
        ),
        ({"SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": "P@ssw0rd123!"}, "P@ssw0rd123!"),
        ({"SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_private_key_passphrase(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_private_key_passphrase()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_TOKEN_FILE_PATH": "/path/to/token.txt"}, "/path/to/token.txt"),
        (
            {"SNOWFLAKE_TOKEN_FILE_PATH": "/home/user/.snowflake/oauth_token"},
            "/home/user/.snowflake/oauth_token",
        ),
        ({"SNOWFLAKE_TOKEN_FILE_PATH": "~/tokens/oauth.token"}, "~/tokens/oauth.token"),
        ({"SNOWFLAKE_TOKEN_FILE_PATH": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_token_file_path(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_token_file_path()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        (
            {"SNOWFLAKE_CONNECTIONS_FILE_PATH": "/path/to/connections.toml"},
            "/path/to/connections.toml",
        ),
        (
            {"SNOWFLAKE_CONNECTIONS_FILE_PATH": "/home/user/.snowflake/connections.toml"},
            "/home/user/.snowflake/connections.toml",
        ),
        (
            {"SNOWFLAKE_CONNECTIONS_FILE_PATH": "~/config/connections.toml"},
            "~/config/connections.toml",
        ),
        ({"SNOWFLAKE_CONNECTIONS_FILE_PATH": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_connections_file_path(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_connections_file_path()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected_env_value",
    [
        ({"SNOWFLAKE_HOME": "/custom/snowflake"}, "/custom/snowflake"),
        ({"SNOWFLAKE_HOME": "~/.snowflake"}, "~/.snowflake"),
        ({"SNOWFLAKE_HOME": "/opt/snowflake/config"}, "/opt/snowflake/config"),
        ({"SNOWFLAKE_HOME": ""}, None),  # Empty string defaults to Path.home()
        ({}, None),  # Not set defaults to Path.home()
    ],
)
def test_get_snowflake_home(env_vars: dict, expected_env_value: str | None):
    """Test get_snowflake_home returns SNOWFLAKE_HOME env var or defaults to user home"""
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_home()
        if expected_env_value is not None:
            # When SNOWFLAKE_HOME is set to a non-empty value, use it
            assert result == expected_env_value
        else:
            # When SNOWFLAKE_HOME is empty or not set, defaults to user's home directory
            assert result == str(Path.home())


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_DEFAULT_CONNECTION_NAME": "production"}, "production"),
        ({"SNOWFLAKE_DEFAULT_CONNECTION_NAME": "dev"}, "dev"),
        ({"SNOWFLAKE_DEFAULT_CONNECTION_NAME": "default"}, "default"),
        ({"SNOWFLAKE_DEFAULT_CONNECTION_NAME": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_default_connection_name(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_default_connection_name()
        assert result == expected


# YAML Config Version 2 Tests


def test_parse_yaml_v2_with_both_sections():
    """Test parsing YAML v2 with both schemachange and snowflake sections"""
    raw_config = {
        "config-version": 2,
        "schemachange": {
            "root-folder": "./migrations",
            "modules-folder": "./modules",
            "change-history-table": "SCHEMA.TABLE",
            "autocommit": False,
            "vars": {"env": "dev"},
        },
        "snowflake": {
            "account": "myaccount",
            "user": "myuser",
            "role": "MYROLE",
            "client-session-keep-alive": True,
            "login-timeout": 30,
        },
    }

    result = _parse_yaml_v2(raw_config)

    # Check schemachange parameters are flattened to root (kebab-case converted to snake_case)
    assert result["root_folder"] == "./migrations"
    assert result["modules_folder"] == "./modules"
    assert result["change_history_table"] == "SCHEMA.TABLE"
    assert result["autocommit"] is False
    assert result["vars"] == {"env": "dev"}

    # Check snowflake parameters are stored separately (kept as kebab-case for now)
    assert "additional_snowflake_params" in result
    assert result["additional_snowflake_params"]["account"] == "myaccount"
    assert result["additional_snowflake_params"]["user"] == "myuser"
    assert result["additional_snowflake_params"]["role"] == "MYROLE"
    assert result["additional_snowflake_params"]["client-session-keep-alive"] is True
    assert result["additional_snowflake_params"]["login-timeout"] == 30

    # Check config-version is preserved
    assert result["config-version"] == 2


def test_parse_yaml_v2_with_only_schemachange_section():
    """Test parsing YAML v2 with only schemachange section"""
    raw_config = {"config-version": 2, "schemachange": {"root-folder": "./migrations", "autocommit": True}}

    result = _parse_yaml_v2(raw_config)

    assert result["root_folder"] == "./migrations"  # Converted to snake_case
    assert result["autocommit"] is True
    assert "additional_snowflake_params" not in result
    assert result["config-version"] == 2


def test_parse_yaml_v2_with_only_snowflake_section():
    """Test parsing YAML v2 with only snowflake section"""
    raw_config = {"config-version": 2, "snowflake": {"account": "myaccount", "warehouse": "WH"}}

    result = _parse_yaml_v2(raw_config)

    assert "additional_snowflake_params" in result
    assert result["additional_snowflake_params"]["account"] == "myaccount"
    assert result["additional_snowflake_params"]["warehouse"] == "WH"
    assert result["config-version"] == 2


def test_parse_yaml_v2_with_empty_sections():
    """Test parsing YAML v2 with empty sections"""
    raw_config = {"config-version": 2, "schemachange": {}, "snowflake": {}}

    result = _parse_yaml_v2(raw_config)

    assert result["config-version"] == 2
    assert "additional_snowflake_params" not in result


def test_load_yaml_config_v2_format(tmp_path):
    """Test loading YAML v2 config file"""
    config_file = tmp_path / "config-v2.yml"
    config_file.write_text("""
config-version: 2

schemachange:
  root-folder: './v2-migrations'
  modules-folder: './v2-modules'
  autocommit: true
  vars:
    key1: value1

snowflake:
  account: v2-account
  user: v2-user
  warehouse: V2_WH
  client-session-keep-alive: true
""")

    result = load_yaml_config(config_file)

    # Check schemachange parameters (converted to snake_case)
    assert result["root_folder"] == "./v2-migrations"
    assert result["modules_folder"] == "./v2-modules"
    assert result["autocommit"] is True
    assert result["vars"] == {"key1": "value1"}

    # Check snowflake parameters (kept as kebab-case in additional_snowflake_params)
    assert "additional_snowflake_params" in result
    assert result["additional_snowflake_params"]["account"] == "v2-account"
    assert result["additional_snowflake_params"]["user"] == "v2-user"
    assert result["additional_snowflake_params"]["warehouse"] == "V2_WH"
    assert result["additional_snowflake_params"]["client-session-keep-alive"] is True


def test_load_yaml_config_v1_format(tmp_path):
    """Test loading YAML v1 config file (backward compatibility)"""
    config_file = tmp_path / "config-v1.yml"
    config_file.write_text("""
config-version: 1

root-folder: './v1-migrations'
modules-folder: './v1-modules'
snowflake-account: v1-account
snowflake-user: v1-user
autocommit: false
""")

    result = load_yaml_config(config_file)

    # Check v1 format is preserved (flat structure)
    assert result["root-folder"] == "./v1-migrations"
    assert result["modules-folder"] == "./v1-modules"
    assert result["snowflake-account"] == "v1-account"
    assert result["snowflake-user"] == "v1-user"
    assert result["autocommit"] is False
    assert "additional_snowflake_params" not in result


def test_load_yaml_config_no_version_defaults_to_v1(tmp_path):
    """Test that missing config-version defaults to v1"""
    config_file = tmp_path / "config-no-version.yml"
    config_file.write_text("""
root-folder: './default-migrations'
snowflake-account: default-account
autocommit: true
""")

    result = load_yaml_config(config_file)

    # Should be treated as v1 (flat structure)
    assert result["root-folder"] == "./default-migrations"
    assert result["snowflake-account"] == "default-account"
    assert result["autocommit"] is True
    assert "additional_snowflake_params" not in result


def test_load_yaml_config_invalid_version(tmp_path):
    """Test that invalid config-version raises error"""
    config_file = tmp_path / "config-invalid-version.yml"
    config_file.write_text("""
config-version: 99

root-folder: './migrations'
""")

    with pytest.raises(ValueError, match="Unsupported config-version: 99"):
        load_yaml_config(config_file)


def test_load_yaml_config_nonexistent_file():
    """Test loading nonexistent config file returns empty dict"""
    result = load_yaml_config(Path("/nonexistent/config.yml"))
    assert result == {}


def test_load_yaml_config_none_path():
    """Test loading None config file returns empty dict"""
    result = load_yaml_config(None)
    assert result == {}


def test_get_connections_toml_session_parameters(tmp_path):
    """Test reading session parameters from connections.toml"""
    # Create a temporary connections.toml file
    toml_file = tmp_path / "connections.toml"
    toml_content = """
[production]
account = "myaccount"
user = "myuser"

[production.parameters]
QUERY_TAG = "my_app"
QUOTED_IDENTIFIERS_IGNORE_CASE = false
TIMESTAMP_OUTPUT_FORMAT = "YYYY-MM-DD HH24:MI:SS"

[development]
account = "devaccount"
user = "devuser"

[development.parameters]
QUERY_TAG = "dev_app"
"""
    toml_file.write_text(toml_content)

    # Test reading production connection parameters
    result = get_connections_toml_session_parameters(toml_file, "production")
    assert result == {
        "QUERY_TAG": "my_app",
        "QUOTED_IDENTIFIERS_IGNORE_CASE": False,
        "TIMESTAMP_OUTPUT_FORMAT": "YYYY-MM-DD HH24:MI:SS",
    }

    # Test reading development connection parameters
    result = get_connections_toml_session_parameters(toml_file, "development")
    assert result == {
        "QUERY_TAG": "dev_app",
    }


def test_get_connections_toml_session_parameters_nonexistent_connection(tmp_path):
    """Test that non-existent connection returns empty dict"""
    toml_file = tmp_path / "connections.toml"
    toml_content = """
[production]
account = "myaccount"
"""
    toml_file.write_text(toml_content)

    result = get_connections_toml_session_parameters(toml_file, "nonexistent")
    assert result == {}


def test_get_connections_toml_session_parameters_no_parameters_section(tmp_path):
    """Test that connection without parameters section returns empty dict"""
    toml_file = tmp_path / "connections.toml"
    toml_content = """
[production]
account = "myaccount"
user = "myuser"
"""
    toml_file.write_text(toml_content)

    result = get_connections_toml_session_parameters(toml_file, "production")
    assert result == {}


def test_get_connections_toml_session_parameters_nonexistent_file():
    """Test that nonexistent file returns empty dict"""
    result = get_connections_toml_session_parameters(Path("/nonexistent/connections.toml"), "production")
    assert result == {}


def test_get_connections_toml_session_parameters_none_inputs():
    """Test that None connection_name returns empty dict"""
    result = get_connections_toml_session_parameters(None, None)
    assert result == {}

    result = get_connections_toml_session_parameters(Path("connections.toml"), None)
    assert result == {}

    # When connection_name is provided but path is None, it tries to use default ~/.snowflake/connections.toml
    # This will return empty dict if the file doesn't exist
    result = get_connections_toml_session_parameters(None, "production")
    # Result depends on whether ~/.snowflake/connections.toml exists, so we just check it returns a dict
    assert isinstance(result, dict)


def test_validate_file_path_with_tilde_expansion(tmp_path):
    """Test that validate_file_path expands ~ to home directory"""
    # Create a test file in a subdirectory under home
    home = Path.home()
    test_dir = home / ".schemachange_test_temp"
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "test_connections.toml"

    try:
        # Create test file
        test_file.write_text("[test]\naccount = 'test'\n")

        # Test with tilde path
        relative_to_home = test_file.relative_to(home)
        tilde_path = f"~/{relative_to_home}"

        result = validate_file_path(tilde_path)
        assert result is not None
        assert result.is_absolute()
        assert result == test_file
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
        if test_dir.exists():
            test_dir.rmdir()


def test_validate_file_path_nonexistent_with_tilde():
    """Test that validate_file_path with nonexistent file raises error even with tilde"""
    with pytest.raises(ValueError, match="invalid file path"):
        validate_file_path("~/nonexistent_file_that_does_not_exist.toml")
