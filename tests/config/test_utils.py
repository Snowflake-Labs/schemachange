from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.utils import (
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
            {
                "SNOWFLAKE_CONNECTIONS_FILE_PATH": "/home/user/.snowflake/connections.toml"
            },
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
    "env_vars, expected",
    [
        ({"SNOWFLAKE_HOME": "/custom/snowflake"}, "/custom/snowflake"),
        ({"SNOWFLAKE_HOME": "~/.snowflake"}, "~/.snowflake"),
        ({"SNOWFLAKE_HOME": "/opt/snowflake/config"}, "/opt/snowflake/config"),
        ({"SNOWFLAKE_HOME": ""}, None),
        ({}, None),
    ],
)
def test_get_snowflake_home(env_vars: dict, expected: str | None):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_home()
        assert result == expected


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
