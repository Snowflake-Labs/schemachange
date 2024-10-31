from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.utils import (
    get_snowflake_password,
    get_env_kwargs,
    get_connection_kwargs,
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
        (
            {"SNOWSQL_PWD": "ignored", "SNOWFLAKE_PASSWORD": "my_snowflake_password"},
            {"snowflake_password": "my_snowflake_password"},
        ),
        (
            {"SNOWSQL_PWD": "my_snowflake_password"},
            {"snowflake_password": "my_snowflake_password"},
        ),
        (
            {"SNOWFLAKE_PASSWORD": "my_snowflake_password"},
            {"snowflake_password": "my_snowflake_password"},
        ),
        (
            {"SNOWFLAKE_PRIVATE_KEY_PATH": "my_snowflake_private_key_path"},
            {"snowflake_private_key_path": "my_snowflake_private_key_path"},
        ),
        (
            {"SNOWFLAKE_AUTHENTICATOR": "my_snowflake_authenticator"},
            {"snowflake_authenticator": "my_snowflake_authenticator"},
        ),
        (
            {"SNOWFLAKE_DEFAULT_CONNECTION_NAME": "my_connection_name"},
            {"connection_name": "my_connection_name"},
        ),
    ],
)
def test_get_env_kwargs(env_vars: dict, expected: str):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_env_kwargs()
        assert result == expected


class TestGetConnectionKwargs:
    @mock.patch("pathlib.Path.is_dir", side_effect=[True, True])
    @mock.patch("pathlib.Path.is_file", return_value=False)
    def test_get_connection_kwargs_invalid_connections_file_path(self, _, __):
        with pytest.raises(Exception) as e_info:
            get_connection_kwargs(
                connections_file_path=Path("invalid_connections_file_path"),
                connection_name="invalid_connection_name",
            )

        e_info_value = str(e_info.value)
        assert "invalid file path: invalid_connections_file_path" in e_info_value

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_get_connection_kwargs_no_connection_name(self, _):
        connection_kwargs = get_connection_kwargs(
            connections_file_path=assets_path / "connections.toml",
            connection_name=None,
        )
        assert connection_kwargs == {}

    @mock.patch("pathlib.Path.is_dir", side_effect=[True, True])
    def test_get_connection_kwargs_invalid_connection_name(self, _):
        with pytest.raises(Exception) as e_info:
            get_connection_kwargs(
                connections_file_path=assets_path / "connections.toml",
                connection_name="invalid_connection_name",
            )
        e_info_value = str(e_info.value)
        assert "Invalid connection_name 'invalid_connection_name'" in e_info_value

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_get_connection_kwargs_happy_path(self, _):
        connection_kwargs = get_connection_kwargs(
            connections_file_path=assets_path / "connections.toml",
            connection_name="myconnection",
        )
        assert connection_kwargs == {
            "snowflake_account": "connections.toml-account",
            "snowflake_authenticator": "connections.toml-authenticator",
            "snowflake_database": "connections.toml-database",
            "snowflake_token_path": "connections.toml-token_file_path",
            "snowflake_password": "connections.toml-password",
            "snowflake_private_key_path": "connections.toml-private-key",
            "snowflake_role": "connections.toml-role",
            "snowflake_schema": "connections.toml-schema",
            "snowflake_user": "connections.toml-user",
            "snowflake_warehouse": "connections.toml-warehouse",
        }
