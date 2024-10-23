from __future__ import annotations

from pathlib import Path
from unittest import mock
from unittest.mock import mock_open

import pytest

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.DeployConfig import DeployConfig


@mock.patch("pathlib.Path.is_dir", side_effect=[False])
def test_invalid_root_folder(_):
    with pytest.raises(Exception) as e_info:
        DeployConfig.factory(
            config_file_path=Path("some_config_file_name"),
            root_folder="some_root_folder_name",
            modules_folder="some_modules_folder_name",
            config_vars={"some": "config_vars"},
            snowflake_account="some_snowflake_account",
            snowflake_user="some_snowflake_user",
            snowflake_role="some_snowflake_role",
            snowflake_warehouse="some_snowflake_warehouse",
            snowflake_database="some_snowflake_database",
            snowflake_schema="some_snowflake_schema",
            change_history_table="some_history_table",
            query_tag="some_query_tag",
            oauth_config={"some": "values"},
        )
    e_info_value = str(e_info.value)
    assert "Path is not valid directory: some_root_folder_name" in e_info_value


@mock.patch("pathlib.Path.is_dir", side_effect=[True, False])
def test_invalid_modules_folder(_):
    with pytest.raises(Exception) as e_info:
        DeployConfig.factory(
            config_file_path=Path("some_config_file_name"),
            root_folder="some_root_folder_name",
            modules_folder="some_modules_folder_name",
            config_vars={"some": "config_vars"},
            snowflake_account="some_snowflake_account",
            snowflake_user="some_snowflake_user",
            snowflake_role="some_snowflake_role",
            snowflake_warehouse="some_snowflake_warehouse",
            snowflake_database="some_snowflake_database",
            snowflake_schema="some_snowflake_schema",
            change_history_table="some_history_table",
            query_tag="some_query_tag",
            oauth_config={"some": "values"},
        )
    e_info_value = str(e_info.value)
    assert "Path is not valid directory: some_modules_folder_name" in e_info_value


@mock.patch("pathlib.Path.is_dir", side_effect=[True, True])
@mock.patch("pathlib.Path.is_file", side_effect=[False])
def test_invalid_snowflake_private_key_path(_, __):
    connections_file_path = Path(__file__).parent / "connections.toml"
    connection_name = "myconnection"

    with pytest.raises(Exception) as e_info:
        DeployConfig.factory(
            config_file_path=Path("some_config_file_name"),
            root_folder="some_root_folder_name",
            modules_folder="some_modules_folder_name",
            config_vars={"some": "config_vars"},
            snowflake_account="some_snowflake_account",
            snowflake_user="some_snowflake_user",
            snowflake_role="some_snowflake_role",
            snowflake_warehouse="some_snowflake_warehouse",
            snowflake_database="some_snowflake_database",
            snowflake_schema="some_snowflake_schema",
            snowflake_private_key_path="invalid_snowflake_private_key_path",
            snowflake_token_path="invalid_snowflake_token_path",
            connections_file_path=str(connections_file_path),
            connection_name=connection_name,
            change_history_table="some_history_table",
            query_tag="some_query_tag",
            oauth_config={"some": "values"},
        )
    e_info_value = str(e_info.value)
    assert "invalid file path: invalid_snowflake_private_key_path" in e_info_value


@mock.patch("pathlib.Path.is_dir", side_effect=[True, True])
@mock.patch("pathlib.Path.is_file", side_effect=[True, False])
def test_invalid_snowflake_token_path(_, __):
    connections_file_path = Path(__file__).parent / "connections.toml"
    connection_name = "myconnection"

    with pytest.raises(Exception) as e_info:
        DeployConfig.factory(
            config_file_path=Path("some_config_file_name"),
            root_folder="some_root_folder_name",
            modules_folder="some_modules_folder_name",
            config_vars={"some": "config_vars"},
            snowflake_account="some_snowflake_account",
            snowflake_user="some_snowflake_user",
            snowflake_role="some_snowflake_role",
            snowflake_warehouse="some_snowflake_warehouse",
            snowflake_database="some_snowflake_database",
            snowflake_schema="some_snowflake_schema",
            snowflake_private_key_path="valid_snowflake_private_key_path",
            snowflake_token_path="invalid_snowflake_token_path",
            connections_file_path=str(connections_file_path),
            connection_name=connection_name,
            change_history_table="some_history_table",
            query_tag="some_query_tag",
            oauth_config={"some": "values"},
        )
    e_info_value = str(e_info.value)
    assert "invalid file path: invalid_snowflake_token_path" in e_info_value


def test_config_vars_not_a_dict():
    with pytest.raises(Exception) as e_info:
        BaseConfig.factory(
            subcommand="deploy",
            config_vars="a string",
            config_file_path=Path("."),
        )
    assert "config_vars did not parse correctly, please check its configuration" in str(
        e_info.value
    )


def test_config_vars_reserved_word():
    with pytest.raises(Exception) as e_info:
        BaseConfig.factory(
            subcommand="deploy",
            config_vars={"schemachange": "not allowed"},
            config_file_path=Path("."),
        )
    assert (
        "The variable 'schemachange' has been reserved for use by schemachange, please use a different name"
        in str(e_info.value)
    )


def test_check_for_deploy_args_oauth_with_token_happy_path():
    config = DeployConfig.factory(
        snowflake_account="account",
        snowflake_user="user",
        snowflake_role="role",
        snowflake_warehouse="warehouse",
        snowflake_authenticator="oauth",
        snowflake_oauth_token="my-oauth-token",
        config_file_path=Path("."),
    )
    config.check_for_deploy_args()


@mock.patch("pathlib.Path.is_file", return_value=True)
def test_check_for_deploy_args_oauth_with_file_happy_path(_):
    with mock.patch("builtins.open", mock_open(read_data="my-oauth-token-from-a-file")):
        config = DeployConfig.factory(
            snowflake_account="account",
            snowflake_user="user",
            snowflake_role="role",
            snowflake_warehouse="warehouse",
            snowflake_authenticator="oauth",
            snowflake_token_path="token_path",
            config_file_path=Path("."),
        )
        config.check_for_deploy_args()
        assert config.snowflake_oauth_token == "my-oauth-token-from-a-file"


@mock.patch("schemachange.config.DeployConfig.get_oauth_token")
def test_check_for_deploy_args_oauth_with_request_happy_path(mock_get_oauth_token):
    oauth_token = "my-oauth-token-from-a-request"
    mock_get_oauth_token.return_value = oauth_token
    oauth_config = {"my_oauth_config": "values"}
    config = DeployConfig.factory(
        snowflake_account="account",
        snowflake_user="user",
        snowflake_role="role",
        snowflake_warehouse="warehouse",
        snowflake_authenticator="oauth",
        oauth_config=oauth_config,
        config_file_path=Path("."),
    )
    config.check_for_deploy_args()
    assert config.snowflake_oauth_token == oauth_token
    mock_get_oauth_token.call_args.args[0] == oauth_config


def test_check_for_deploy_args_externalbrowser_happy_path():
    config = DeployConfig.factory(
        snowflake_account="account",
        snowflake_user="user",
        snowflake_role="role",
        snowflake_warehouse="warehouse",
        snowflake_authenticator="externalbrowser",
        config_file_path=Path("."),
    )
    config.check_for_deploy_args()


def test_check_for_deploy_args_okta_happy_path():
    config = DeployConfig.factory(
        snowflake_account="account",
        snowflake_user="user",
        snowflake_role="role",
        snowflake_warehouse="warehouse",
        snowflake_authenticator="https://okta...",
        snowflake_password="password",
        config_file_path=Path("."),
    )
    config.check_for_deploy_args()


@mock.patch("pathlib.Path.is_file", return_value=True)
def test_check_for_deploy_args_snowflake_jwt_happy_path(_):
    config = DeployConfig.factory(
        snowflake_account="account",
        snowflake_user="user",
        snowflake_role="role",
        snowflake_warehouse="warehouse",
        snowflake_authenticator="snowflake_jwt",
        snowflake_private_key_path="private_key_path",
        config_file_path=Path("."),
    )
    config.check_for_deploy_args()


def test_check_for_deploy_args_snowflake_happy_path():
    config = DeployConfig.factory(
        snowflake_account="account",
        snowflake_user="user",
        snowflake_role="role",
        snowflake_warehouse="warehouse",
        snowflake_authenticator="snowflake",
        snowflake_password="password",
        config_file_path=Path("."),
    )
    config.check_for_deploy_args()


def test_check_for_deploy_args_default_happy_path():
    config = DeployConfig.factory(
        snowflake_account="account",
        snowflake_user="user",
        snowflake_role="role",
        snowflake_warehouse="warehouse",
        snowflake_password="password",
        config_file_path=Path("."),
    )
    config.check_for_deploy_args()


def test_check_for_deploy_args_exception():
    config = DeployConfig.factory(config_file_path=Path("."))
    with pytest.raises(ValueError) as e:
        config.check_for_deploy_args()

    assert "Missing config values. The following config values are required" in str(
        e.value
    )
