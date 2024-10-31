import json
import logging
import os

import structlog
import tomlkit
from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.get_merged_config import (
    get_merged_config,
    get_yaml_config_kwargs,
)

default_cli_kwargs = {
    "subcommand": "deploy",
    "config_file_name": "schemachange-config.yml",
    "config_vars": {},
}

assets_path = Path(__file__).parent


def get_connection_from_toml(file_path: Path, connection_name: str) -> dict:
    with file_path.open("rb") as f:
        connections = tomlkit.load(f)
        return connections[connection_name]


my_connection = get_connection_from_toml(
    file_path=assets_path / "connections.toml", connection_name="myconnection"
)

alt_connection = get_connection_from_toml(
    file_path=assets_path / "alt-connections.toml",
    connection_name="myaltconnection",
)

schemachange_config = get_yaml_config_kwargs(assets_path / "schemachange-config.yml")
schemachange_config_full = get_yaml_config_kwargs(
    assets_path / "schemachange-config-full.yml"
)
schemachange_config_full_no_connection = get_yaml_config_kwargs(
    assets_path / "schemachange-config-full-no-connection.yml"
)
schemachange_config_partial_with_connection = get_yaml_config_kwargs(
    assets_path / "schemachange-config-partial-with-connection.yml"
)


@pytest.mark.parametrize(
    "env_kwargs, cli_kwargs, yaml_kwargs, connection_kwargs, expected",
    [
        pytest.param(
            {},  # env_kwargs
            {**default_cli_kwargs},  # cli_kwargs
            {},  # yaml_kwargs
            {},  # connection_kwargs
            {  # expected
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
            },
            id="Deploy: Only required arguments",
        ),
        pytest.param(
            {},  # env_kwargs
            {**default_cli_kwargs},  # cli_kwargs
            {},  # yaml_kwargs
            {  # connection_kwargs
                "snowflake_account": "connection_snowflake_account",
                "snowflake_user": "connection_snowflake_user",
                "snowflake_role": "connection_snowflake_role",
                "snowflake_warehouse": "connection_snowflake_warehouse",
                "snowflake_database": "connection_snowflake_database",
                "snowflake_schema": "connection_snowflake_schema",
                "snowflake_authenticator": "connection_snowflake_authenticator",
                "snowflake_password": "connection_snowflake_password",
                "snowflake_private_key_path": "connection_snowflake_private_key_path",
                "snowflake_token_path": "connection_snowflake_token_path",
            },
            {  # expected
                "log_level": logging.INFO,
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "snowflake_account": "connection_snowflake_account",
                "snowflake_user": "connection_snowflake_user",
                "snowflake_role": "connection_snowflake_role",
                "snowflake_warehouse": "connection_snowflake_warehouse",
                "snowflake_database": "connection_snowflake_database",
                "snowflake_schema": "connection_snowflake_schema",
                "snowflake_authenticator": "connection_snowflake_authenticator",
                "snowflake_password": "connection_snowflake_password",
                "snowflake_private_key_path": "connection_snowflake_private_key_path",
                "snowflake_token_path": "connection_snowflake_token_path",
            },
            id="Deploy: all connection_kwargs",
        ),
        pytest.param(
            {},  # env_kwargs
            {**default_cli_kwargs},  # cli_kwargs
            {  # yaml_kwargs
                "root_folder": "yaml_root_folder",
                "modules_folder": "yaml_modules_folder",
                "config_vars": {
                    "variable_1": "yaml_variable_1",
                    "variable_2": "yaml_variable_2",
                    "variable_3": "yaml_variable_3",
                },
                "log_level": logging.DEBUG,
                "snowflake_account": "yaml_snowflake_account",
                "snowflake_user": "yaml_snowflake_user",
                "snowflake_role": "yaml_snowflake_role",
                "snowflake_warehouse": "yaml_snowflake_warehouse",
                "snowflake_database": "yaml_snowflake_database",
                "snowflake_schema": "yaml_snowflake_schema",
                "snowflake_authenticator": "yaml_snowflake_authenticator",
                "snowflake_private_key_path": "yaml_snowflake_private_key_path",
                "snowflake_token_path": "yaml_snowflake_token_path",
                "connections_file_path": "yaml_connections_file_path",
                "connection_name": "yaml_connection_name",
                "change_history_table": "yaml_change_history_table",
                "create_change_history_table": True,
                "autocommit": True,
                "dry_run": True,
                "query_tag": "yaml_query_tag",
                "oauth_config": {"oauth_config_variable": "yaml_oauth_config_value"},
            },
            {  # connection_kwargs
                "snowflake_account": "connection_snowflake_account",
                "snowflake_user": "connection_snowflake_user",
                "snowflake_role": "connection_snowflake_role",
                "snowflake_warehouse": "connection_snowflake_warehouse",
                "snowflake_database": "connection_snowflake_database",
                "snowflake_schema": "connection_snowflake_schema",
                "snowflake_authenticator": "connection_snowflake_authenticator",
                "snowflake_password": "connection_snowflake_password",
                "snowflake_private_key_path": "connection_snowflake_private_key_path",
                "snowflake_token_path": "connection_snowflake_token_path",
            },
            {  # expected
                "log_level": logging.DEBUG,
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {
                    "variable_1": "yaml_variable_1",
                    "variable_2": "yaml_variable_2",
                    "variable_3": "yaml_variable_3",
                },
                "subcommand": "deploy",
                "root_folder": "yaml_root_folder",
                "modules_folder": "yaml_modules_folder",
                "snowflake_account": "yaml_snowflake_account",
                "snowflake_user": "yaml_snowflake_user",
                "snowflake_role": "yaml_snowflake_role",
                "snowflake_warehouse": "yaml_snowflake_warehouse",
                "snowflake_database": "yaml_snowflake_database",
                "snowflake_schema": "yaml_snowflake_schema",
                "snowflake_authenticator": "yaml_snowflake_authenticator",
                "snowflake_password": "connection_snowflake_password",
                "snowflake_private_key_path": "yaml_snowflake_private_key_path",
                "snowflake_token_path": "yaml_snowflake_token_path",
                "connections_file_path": Path("yaml_connections_file_path"),
                "connection_name": "yaml_connection_name",
                "change_history_table": "yaml_change_history_table",
                "create_change_history_table": True,
                "autocommit": True,
                "dry_run": True,
                "query_tag": "yaml_query_tag",
                "oauth_config": {"oauth_config_variable": "yaml_oauth_config_value"},
            },
            id="Deploy: all yaml, all connection_kwargs",
        ),
        pytest.param(
            {},  # env_kwargs
            {  # cli_kwargs
                **default_cli_kwargs,
                "config_folder": "cli_config_folder",
                "root_folder": "cli_root_folder",
                "modules_folder": "cli_modules_folder",
                "config_vars": {
                    "variable_1": "cli_variable_1",
                    "variable_2": "cli_variable_2",
                },
                "log_level": logging.INFO,
                "snowflake_account": "cli_snowflake_account",
                "snowflake_user": "cli_snowflake_user",
                "snowflake_role": "cli_snowflake_role",
                "snowflake_warehouse": "cli_snowflake_warehouse",
                "snowflake_database": "cli_snowflake_database",
                "snowflake_schema": "cli_snowflake_schema",
                "snowflake_authenticator": "cli_snowflake_authenticator",
                "snowflake_private_key_path": "cli_snowflake_private_key_path",
                "snowflake_token_path": "cli_snowflake_token_path",
                "connections_file_path": "cli_connections_file_path",
                "connection_name": "cli_connection_name",
                "change_history_table": "cli_change_history_table",
                "create_change_history_table": False,
                "autocommit": False,
                "dry_run": False,
                "query_tag": "cli_query_tag",
                "oauth_config": {"oauth_config_variable": "cli_oauth_config_value"},
            },
            {  # yaml_kwargs
                "root_folder": "yaml_root_folder",
                "modules_folder": "yaml_modules_folder",
                "config_vars": {
                    "variable_1": "yaml_variable_1",
                    "variable_2": "yaml_variable_2",
                    "variable_3": "yaml_variable_3",
                },
                "log_level": logging.DEBUG,
                "snowflake_account": "yaml_snowflake_account",
                "snowflake_user": "yaml_snowflake_user",
                "snowflake_role": "yaml_snowflake_role",
                "snowflake_warehouse": "yaml_snowflake_warehouse",
                "snowflake_database": "yaml_snowflake_database",
                "snowflake_schema": "yaml_snowflake_schema",
                "snowflake_authenticator": "yaml_snowflake_authenticator",
                "snowflake_private_key_path": "yaml_snowflake_private_key_path",
                "snowflake_token_path": "yaml_snowflake_token_path",
                "connections_file_path": "yaml_connections_file_path",
                "connection_name": "yaml_connection_name",
                "change_history_table": "yaml_change_history_table",
                "create_change_history_table": True,
                "autocommit": True,
                "dry_run": True,
                "query_tag": "yaml_query_tag",
                "oauth_config": {"oauth_config_variable": "yaml_oauth_config_value"},
            },
            {  # connection_kwargs
                "snowflake_account": "connection_snowflake_account",
                "snowflake_user": "connection_snowflake_user",
                "snowflake_role": "connection_snowflake_role",
                "snowflake_warehouse": "connection_snowflake_warehouse",
                "snowflake_database": "connection_snowflake_database",
                "snowflake_schema": "connection_snowflake_schema",
                "snowflake_authenticator": "connection_snowflake_authenticator",
                "snowflake_password": "connection_snowflake_password",
                "snowflake_private_key_path": "connection_snowflake_private_key_path",
                "snowflake_token_path": "connection_snowflake_token_path",
            },
            {  # expected
                "log_level": logging.INFO,
                "config_file_path": Path("cli_config_folder/schemachange-config.yml"),
                "config_vars": {
                    "variable_1": "cli_variable_1",
                    "variable_2": "cli_variable_2",
                    "variable_3": "yaml_variable_3",
                },
                "subcommand": "deploy",
                "root_folder": "cli_root_folder",
                "modules_folder": "cli_modules_folder",
                "snowflake_account": "cli_snowflake_account",
                "snowflake_user": "cli_snowflake_user",
                "snowflake_role": "cli_snowflake_role",
                "snowflake_warehouse": "cli_snowflake_warehouse",
                "snowflake_database": "cli_snowflake_database",
                "snowflake_schema": "cli_snowflake_schema",
                "snowflake_authenticator": "cli_snowflake_authenticator",
                "snowflake_password": "connection_snowflake_password",
                "snowflake_private_key_path": "cli_snowflake_private_key_path",
                "snowflake_token_path": "cli_snowflake_token_path",
                "connections_file_path": Path("cli_connections_file_path"),
                "connection_name": "cli_connection_name",
                "change_history_table": "cli_change_history_table",
                "create_change_history_table": False,
                "autocommit": False,
                "dry_run": False,
                "query_tag": "cli_query_tag",
                "oauth_config": {"oauth_config_variable": "cli_oauth_config_value"},
            },
            id="Deploy: all cli, all yaml, all connection_kwargs",
        ),
        pytest.param(
            {  # env_kwargs
                "snowflake_password": "env_snowflake_password",
                "snowflake_private_key_path": "env_snowflake_private_key_path",
                "snowflake_authenticator": "env_snowflake_authenticator",
                "connection_name": "env_connection_name",
            },
            {  # cli_kwargs
                **default_cli_kwargs,
                "config_folder": "cli_config_folder",
                "root_folder": "cli_root_folder",
                "modules_folder": "cli_modules_folder",
                "config_vars": {
                    "variable_1": "cli_variable_1",
                    "variable_2": "cli_variable_2",
                },
                "log_level": logging.INFO,
                "snowflake_account": "cli_snowflake_account",
                "snowflake_user": "cli_snowflake_user",
                "snowflake_role": "cli_snowflake_role",
                "snowflake_warehouse": "cli_snowflake_warehouse",
                "snowflake_database": "cli_snowflake_database",
                "snowflake_schema": "cli_snowflake_schema",
                "snowflake_authenticator": "cli_snowflake_authenticator",
                "snowflake_private_key_path": "cli_snowflake_private_key_path",
                "snowflake_token_path": "cli_snowflake_token_path",
                "connections_file_path": "cli_connections_file_path",
                "connection_name": "cli_connection_name",
                "change_history_table": "cli_change_history_table",
                "create_change_history_table": False,
                "autocommit": False,
                "dry_run": False,
                "query_tag": "cli_query_tag",
                "oauth_config": {"oauth_config_variable": "cli_oauth_config_value"},
            },
            {  # yaml_kwargs
                "root_folder": "yaml_root_folder",
                "modules_folder": "yaml_modules_folder",
                "config_vars": {
                    "variable_1": "yaml_variable_1",
                    "variable_2": "yaml_variable_2",
                    "variable_3": "yaml_variable_3",
                },
                "log_level": logging.DEBUG,
                "snowflake_account": "yaml_snowflake_account",
                "snowflake_user": "yaml_snowflake_user",
                "snowflake_role": "yaml_snowflake_role",
                "snowflake_warehouse": "yaml_snowflake_warehouse",
                "snowflake_database": "yaml_snowflake_database",
                "snowflake_schema": "yaml_snowflake_schema",
                "snowflake_authenticator": "yaml_snowflake_authenticator",
                "snowflake_private_key_path": "yaml_snowflake_private_key_path",
                "snowflake_token_path": "yaml_snowflake_token_path",
                "connections_file_path": "yaml_connections_file_path",
                "connection_name": "yaml_connection_name",
                "change_history_table": "yaml_change_history_table",
                "create_change_history_table": True,
                "autocommit": True,
                "dry_run": True,
                "query_tag": "yaml_query_tag",
                "oauth_config": {"oauth_config_variable": "yaml_oauth_config_value"},
            },
            {  # connection_kwargs
                "snowflake_account": "connection_snowflake_account",
                "snowflake_user": "connection_snowflake_user",
                "snowflake_role": "connection_snowflake_role",
                "snowflake_warehouse": "connection_snowflake_warehouse",
                "snowflake_database": "connection_snowflake_database",
                "snowflake_schema": "connection_snowflake_schema",
                "snowflake_authenticator": "connection_snowflake_authenticator",
                "snowflake_password": "connection_snowflake_password",
                "snowflake_private_key_path": "connection_snowflake_private_key_path",
                "snowflake_token_path": "connection_snowflake_token_path",
            },
            {  # expected
                "log_level": logging.INFO,
                "config_file_path": Path("cli_config_folder/schemachange-config.yml"),
                "config_vars": {
                    "variable_1": "cli_variable_1",
                    "variable_2": "cli_variable_2",
                    "variable_3": "yaml_variable_3",
                },
                "subcommand": "deploy",
                "root_folder": "cli_root_folder",
                "modules_folder": "cli_modules_folder",
                "snowflake_account": "cli_snowflake_account",
                "snowflake_user": "cli_snowflake_user",
                "snowflake_role": "cli_snowflake_role",
                "snowflake_warehouse": "cli_snowflake_warehouse",
                "snowflake_database": "cli_snowflake_database",
                "snowflake_schema": "cli_snowflake_schema",
                "snowflake_authenticator": "env_snowflake_authenticator",
                "snowflake_password": "env_snowflake_password",
                "snowflake_private_key_path": "env_snowflake_private_key_path",
                "snowflake_token_path": "cli_snowflake_token_path",
                "connections_file_path": Path("cli_connections_file_path"),
                "connection_name": "env_connection_name",
                "change_history_table": "cli_change_history_table",
                "create_change_history_table": False,
                "autocommit": False,
                "dry_run": False,
                "query_tag": "cli_query_tag",
                "oauth_config": {"oauth_config_variable": "cli_oauth_config_value"},
            },
            id="Deploy: all env, all cli, all yaml, all connection_kwargs",
        ),
    ],
)
@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("pathlib.Path.is_file", return_value=True)
@mock.patch("schemachange.config.get_merged_config.get_env_kwargs")
@mock.patch("schemachange.config.get_merged_config.parse_cli_args")
@mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs")
@mock.patch("schemachange.config.get_merged_config.get_connection_kwargs")
@mock.patch("schemachange.config.get_merged_config.DeployConfig.factory")
def test_get_merged_config_inheritance(
    mock_deploy_config_factory,
    mock_get_connection_kwargs,
    mock_get_yaml_config_kwargs,
    mock_parse_cli_args,
    mock_get_env_kwargs,
    _,
    __,
    env_kwargs,
    cli_kwargs,
    yaml_kwargs,
    connection_kwargs,
    expected,
):
    mock_get_env_kwargs.return_value = {**env_kwargs}
    mock_parse_cli_args.return_value = {**cli_kwargs}
    mock_get_yaml_config_kwargs.return_value = {**yaml_kwargs}
    mock_get_connection_kwargs.return_value = {**connection_kwargs}
    logger = structlog.testing.CapturingLogger()
    # noinspection PyTypeChecker
    get_merged_config(logger=logger)
    factory_kwargs = mock_deploy_config_factory.call_args.kwargs
    for actual_key, actual_value in factory_kwargs.items():
        assert expected[actual_key] == actual_value


@mock.patch("pathlib.Path.is_dir", return_value=False)
@mock.patch("schemachange.config.get_merged_config.parse_cli_args")
def test_invalid_config_folder(mock_parse_cli_args, _):
    cli_kwargs = {
        "config_folder": "cli_config_folder",
        **default_cli_kwargs,
    }
    mock_parse_cli_args.return_value = {**cli_kwargs}
    logger = structlog.testing.CapturingLogger()
    with pytest.raises(Exception) as e_info:
        # noinspection PyTypeChecker
        get_merged_config(logger=logger)
    assert f"Path is not valid directory: {cli_kwargs['config_folder']}" in str(
        e_info.value
    )


param_only_required_cli_arguments = pytest.param(
    {},  # env_kwargs
    [  # cli_args
        "schemachange",
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": Path("schemachange-config.yml"),
        "config_version": 1,
        "config_vars": {},
        "log_level": logging.INFO,
    },
    id="Deploy: Only required cli arguments",
)

param_full_cli_and_connection = pytest.param(
    {},  # env_kwargs
    [  # cli_args
        "schemachange",
        "--root-folder",
        "root-folder-from-cli",
        "--modules-folder",
        "modules-folder-from-cli",
        "--vars",
        '{"var1": "from_cli", "var3": "also_from_cli"}',
        "--snowflake-account",
        "snowflake-account-from-cli",
        "--snowflake-user",
        "snowflake-user-from-cli",
        "--snowflake-role",
        "snowflake-role-from-cli",
        "--snowflake-warehouse",
        "snowflake-warehouse-from-cli",
        "--snowflake-database",
        "snowflake-database-from-cli",
        "--snowflake-schema",
        "snowflake-schema-from-cli",
        "--snowflake-authenticator",
        "snowflake-authenticator-from-cli",
        "--snowflake-private-key-path",
        "snowflake-private-key-path-from-cli",
        "--snowflake-token-path",
        "snowflake-token-path-from-cli",
        "--connections-file-path",
        str(assets_path / "alt-connections.toml"),
        "--connection-name",
        "myaltconnection",
        "--change-history-table",
        "change-history-table-from-cli",
        "--create-change-history-table",
        "--autocommit",
        "--dry-run",
        "--query-tag",
        "query-tag-from-cli",
        "--oauth-config",
        json.dumps({"oauth_config_variable": "cli_oauth_config_value"}),
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": Path("schemachange-config.yml"),
        "config_version": 1,
        "root_folder": "root-folder-from-cli",
        "modules_folder": "modules-folder-from-cli",
        "snowflake_account": "snowflake-account-from-cli",
        "snowflake_user": "snowflake-user-from-cli",
        "snowflake_role": "snowflake-role-from-cli",
        "snowflake_warehouse": "snowflake-warehouse-from-cli",
        "snowflake_database": "snowflake-database-from-cli",
        "snowflake_schema": "snowflake-schema-from-cli",
        "snowflake_authenticator": "snowflake-authenticator-from-cli",
        "snowflake_private_key_path": "snowflake-private-key-path-from-cli",
        "snowflake_token_path": "snowflake-token-path-from-cli",
        "change_history_table": "change-history-table-from-cli",
        "config_vars": {
            "var1": "from_cli",
            "var3": "also_from_cli",
        },
        "create_change_history_table": True,
        "autocommit": True,
        "log_level": logging.INFO,
        "dry_run": True,
        "query_tag": "query-tag-from-cli",
        "oauth_config": {"oauth_config_variable": "cli_oauth_config_value"},
        "connection_name": "myaltconnection",
        "connections_file_path": assets_path / "alt-connections.toml",
        "snowflake_password": alt_connection["password"],
    },
    id="Deploy: full cli and connections.toml",
)

param_full_yaml_no_connection = pytest.param(
    {},  # env_kwargs
    [  # cli_args
        "schemachange",
        "--config-folder",
        str(assets_path),
        "--config-file-name",
        "schemachange-config-full-no-connection.yml",
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path / "schemachange-config-full-no-connection.yml",
        "log_level": logging.INFO,
        **{
            k: v
            for k, v in schemachange_config_full_no_connection.items()
            if k
            in [
                "config_version",
                "root_folder",
                "modules_folder",
                "snowflake_account",
                "snowflake_user",
                "snowflake_role",
                "snowflake_warehouse",
                "snowflake_database",
                "snowflake_schema",
                "snowflake_authenticator",
                "snowflake_private_key_path",
                "snowflake_token_path",
                "change_history_table",
                "config_vars",
                "create_change_history_table",
                "autocommit",
                "dry_run",
                "query_tag",
                "oauth_config",
            ]
        },
    },
    id="Deploy: yaml, no connections.toml",
)

param_full_yaml_and_connection = pytest.param(
    {},  # env_kwargs
    [  # cli_args
        "schemachange",
        "--config-folder",
        str(assets_path),
        "--config-file-name",
        "schemachange-config-full.yml",
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path / "schemachange-config-full.yml",
        "snowflake_password": my_connection["password"],
        "log_level": logging.INFO,
        "connections_file_path": assets_path / "connections.toml",
        **{
            k: v
            for k, v in schemachange_config_full.items()
            if k
            in [
                "config_version",
                "root_folder",
                "modules_folder",
                "snowflake_account",
                "snowflake_user",
                "snowflake_role",
                "snowflake_warehouse",
                "snowflake_database",
                "snowflake_schema",
                "snowflake_authenticator",
                "snowflake_private_key_path",
                "snowflake_token_path",
                "change_history_table",
                "snowflake_private_key_path",
                "config_vars",
                "create_change_history_table",
                "autocommit",
                "dry_run",
                "query_tag",
                "oauth_config",
                "connection_name",
            ]
        },
    },
    id="Deploy: full yaml and connections.toml",
)

param_full_yaml_and_connection_and_cli = pytest.param(
    {},  # env_kwargs
    [  # cli_args
        "schemachange",
        "--config-folder",
        str(assets_path),
        "--config-file-name",
        "schemachange-config-full.yml",
        "--root-folder",
        "root-folder-from-cli",
        "--modules-folder",
        "modules-folder-from-cli",
        "--vars",
        '{"var1": "from_cli", "var3": "also_from_cli"}',
        "--snowflake-account",
        "snowflake-account-from-cli",
        "--snowflake-user",
        "snowflake-user-from-cli",
        "--snowflake-role",
        "snowflake-role-from-cli",
        "--snowflake-warehouse",
        "snowflake-warehouse-from-cli",
        "--snowflake-database",
        "snowflake-database-from-cli",
        "--snowflake-schema",
        "snowflake-schema-from-cli",
        "--snowflake-authenticator",
        "snowflake-authenticator-from-cli",
        "--snowflake-private-key-path",
        "snowflake-private-key-path-from-cli",
        "--snowflake-token-path",
        "snowflake-token-path-from-cli",
        "--connections-file-path",
        str(assets_path / "alt-connections.toml"),
        "--connection-name",
        "myaltconnection",
        "--change-history-table",
        "change-history-table-from-cli",
        "--create-change-history-table",
        "--autocommit",
        "--dry-run",
        "--query-tag",
        "query-tag-from-cli",
        "--oauth-config",
        json.dumps({"oauth_config_variable": "cli_oauth_config_value"}),
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path / "schemachange-config-full.yml",
        "config_version": 1,
        "root_folder": "root-folder-from-cli",
        "modules_folder": "modules-folder-from-cli",
        "snowflake_account": "snowflake-account-from-cli",
        "snowflake_user": "snowflake-user-from-cli",
        "snowflake_role": "snowflake-role-from-cli",
        "snowflake_warehouse": "snowflake-warehouse-from-cli",
        "snowflake_database": "snowflake-database-from-cli",
        "snowflake_schema": "snowflake-schema-from-cli",
        "snowflake_authenticator": "snowflake-authenticator-from-cli",
        "snowflake_private_key_path": "snowflake-private-key-path-from-cli",
        "snowflake_token_path": "snowflake-token-path-from-cli",
        "change_history_table": "change-history-table-from-cli",
        "config_vars": {
            "var1": "from_cli",
            "var2": "also_from_yaml",
            "var3": "also_from_cli",
        },
        "create_change_history_table": True,
        "autocommit": True,
        "log_level": logging.INFO,
        "dry_run": True,
        "query_tag": "query-tag-from-cli",
        "oauth_config": {"oauth_config_variable": "cli_oauth_config_value"},
        "connection_name": "myaltconnection",
        "connections_file_path": assets_path / "alt-connections.toml",
        "snowflake_password": alt_connection["password"],
    },
    id="Deploy: full yaml, connections.toml, and cli",
)

param_full_yaml_and_connection_and_cli_and_env = pytest.param(
    {
        "SNOWFLAKE_PASSWORD": "env_snowflake_password",
        "SNOWFLAKE_PRIVATE_KEY_PATH": "env_snowflake_private_key_path",
        "SNOWFLAKE_AUTHENTICATOR": "env_snowflake_authenticator",
        "SNOWFLAKE_TOKEN": "env_snowflake_token",
        "SNOWFLAKE_DEFAULT_CONNECTION_NAME": "anotherconnection",
    },  # env_kwargs
    [  # cli_args
        "schemachange",
        "--config-folder",
        str(assets_path),
        "--config-file-name",
        "schemachange-config-full.yml",
        "--root-folder",
        "root-folder-from-cli",
        "--modules-folder",
        "modules-folder-from-cli",
        "--vars",
        '{"var1": "from_cli", "var3": "also_from_cli"}',
        "--snowflake-account",
        "snowflake-account-from-cli",
        "--snowflake-user",
        "snowflake-user-from-cli",
        "--snowflake-role",
        "snowflake-role-from-cli",
        "--snowflake-warehouse",
        "snowflake-warehouse-from-cli",
        "--snowflake-database",
        "snowflake-database-from-cli",
        "--snowflake-schema",
        "snowflake-schema-from-cli",
        "--snowflake-authenticator",
        "snowflake-authenticator-from-cli",
        "--snowflake-private-key-path",
        "snowflake-private-key-path-from-cli",
        "--snowflake-token-path",
        "snowflake-token-path-from-cli",
        "--connections-file-path",
        str(assets_path / "alt-connections.toml"),
        "--connection-name",
        "myaltconnection",
        "--change-history-table",
        "change-history-table-from-cli",
        "--create-change-history-table",
        "--autocommit",
        "--dry-run",
        "--query-tag",
        "query-tag-from-cli",
        "--oauth-config",
        json.dumps({"oauth_config_variable": "cli_oauth_config_value"}),
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path / "schemachange-config-full.yml",
        "config_version": 1,
        "root_folder": "root-folder-from-cli",
        "modules_folder": "modules-folder-from-cli",
        "snowflake_account": "snowflake-account-from-cli",
        "snowflake_user": "snowflake-user-from-cli",
        "snowflake_role": "snowflake-role-from-cli",
        "snowflake_warehouse": "snowflake-warehouse-from-cli",
        "snowflake_database": "snowflake-database-from-cli",
        "snowflake_schema": "snowflake-schema-from-cli",
        "snowflake_authenticator": "env_snowflake_authenticator",
        "snowflake_private_key_path": "env_snowflake_private_key_path",
        "snowflake_token_path": "snowflake-token-path-from-cli",
        "change_history_table": "change-history-table-from-cli",
        "config_vars": {
            "var1": "from_cli",
            "var2": "also_from_yaml",
            "var3": "also_from_cli",
        },
        "create_change_history_table": True,
        "autocommit": True,
        "log_level": logging.INFO,
        "dry_run": True,
        "query_tag": "query-tag-from-cli",
        "snowflake_oauth_token": "env_snowflake_token",
        "oauth_config": {"oauth_config_variable": "cli_oauth_config_value"},
        "connection_name": "anotherconnection",
        "connections_file_path": assets_path / "alt-connections.toml",
        "snowflake_password": "env_snowflake_password",
    },
    id="Deploy: full yaml, connections.toml, cli, and env",
)


param_connection_no_yaml = pytest.param(
    {},  # env_kwargs
    [  # cli_args
        "schemachange",
        "--config-folder",
        str(assets_path),
        "--connections-file-path",
        str(assets_path / "connections.toml"),
        "--connection-name",
        "myconnection",
    ],
    {  # expected
        "subcommand": "deploy",
        "connections_file_path": assets_path / "connections.toml",
        "connection_name": "myconnection",
        "config_file_path": assets_path / "schemachange-config.yml",
        "config_version": 1,
        "snowflake_account": my_connection["account"],
        "snowflake_user": my_connection["user"],
        "snowflake_role": my_connection["role"],
        "snowflake_warehouse": my_connection["warehouse"],
        "snowflake_database": my_connection["database"],
        "snowflake_schema": my_connection["schema"],
        "snowflake_authenticator": my_connection["authenticator"],
        "snowflake_password": my_connection["password"],
        "snowflake_private_key_path": my_connection["private-key"],
        "snowflake_token_path": my_connection["token_file_path"],
        "config_vars": {},
        "log_level": logging.INFO,
    },
    id="Deploy: connections.toml, no yaml",
)

param_partial_yaml_and_connection = pytest.param(
    {},  # env_kwargs
    [  # cli_arg
        "schemachange",
        "--config-folder",
        str(assets_path),
        "--config-file-name",
        "schemachange-config-partial-with-connection.yml",
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path
        / "schemachange-config-partial-with-connection.yml",
        "snowflake_account": my_connection["account"],
        "snowflake_user": my_connection["user"],
        "snowflake_role": my_connection["role"],
        "snowflake_warehouse": my_connection["warehouse"],
        "snowflake_database": my_connection["database"],
        "snowflake_schema": my_connection["schema"],
        "snowflake_authenticator": my_connection["authenticator"],
        "snowflake_private_key_path": my_connection["private-key"],
        "snowflake_token_path": my_connection["token_file_path"],
        "log_level": logging.INFO,
        "snowflake_password": my_connection["password"],
        "connections_file_path": assets_path / "connections.toml",
        **{
            k: v
            for k, v in schemachange_config_partial_with_connection.items()
            if k
            in [
                "config_version",
                "root_folder",
                "modules_folder",
                "change_history_table",
                "config_vars",
                "create_change_history_table",
                "autocommit",
                "dry_run",
                "query_tag",
                "oauth_config",
                "connection_name",
            ]
        },
    },
    id="Deploy: partial yaml and connections.toml",
)


@pytest.mark.parametrize(
    "env_vars, cli_args, expected",
    [
        param_only_required_cli_arguments,
        param_full_cli_and_connection,
        param_full_yaml_no_connection,
        param_full_yaml_and_connection,
        param_full_yaml_and_connection_and_cli,
        param_full_yaml_and_connection_and_cli_and_env,
        param_connection_no_yaml,
        param_partial_yaml_and_connection,
    ],
)
@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.get_merged_config.DeployConfig.factory")
def test_integration_get_merged_config_inheritance(
    mock_deploy_config_factory,
    _,
    env_vars,
    cli_args,
    expected,
):
    logger = structlog.testing.CapturingLogger()
    with mock.patch.dict(os.environ, env_vars, clear=True):
        with mock.patch("sys.argv", cli_args):
            # noinspection PyTypeChecker
            get_merged_config(logger=logger)
            factory_kwargs = mock_deploy_config_factory.call_args.kwargs
            for actual_key, actual_value in factory_kwargs.items():
                assert expected[actual_key] == actual_value
