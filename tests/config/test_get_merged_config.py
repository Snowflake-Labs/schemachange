import logging

import structlog
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
    "cli_kwargs, yaml_kwargs, expected",
    [
        pytest.param(
            {**default_cli_kwargs},  # cli_kwargs
            {},  # yaml_kwargs
            {  # expected
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
            },
            id="Deploy: Only required arguments",
        ),
        pytest.param(
            {**default_cli_kwargs},  # cli_kwargs
            {},  # yaml_kwargs
            {  # expected
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
            },
            id="Deploy: all connection_kwargs",
        ),
        pytest.param(
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
                "connections_file_path": "yaml_connections_file_path",
                "connection_name": "yaml_connection_name",
                "change_history_table": "yaml_change_history_table",
                "create_change_history_table": True,
                "autocommit": True,
                "dry_run": True,
                "query_tag": "yaml_query_tag",
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
                "connections_file_path": Path("yaml_connections_file_path"),
                "connection_name": "yaml_connection_name",
                "change_history_table": "yaml_change_history_table",
                "create_change_history_table": True,
                "autocommit": True,
                "dry_run": True,
                "query_tag": "yaml_query_tag",
            },
            id="Deploy: all yaml, all connection_kwargs",
        ),
        pytest.param(
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
                "connections_file_path": "cli_connections_file_path",
                "connection_name": "cli_connection_name",
                "change_history_table": "cli_change_history_table",
                "create_change_history_table": False,
                "autocommit": False,
                "dry_run": False,
                "query_tag": "cli_query_tag",
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
                "connections_file_path": "yaml_connections_file_path",
                "connection_name": "yaml_connection_name",
                "change_history_table": "yaml_change_history_table",
                "create_change_history_table": True,
                "autocommit": True,
                "dry_run": True,
                "query_tag": "yaml_query_tag",
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
                "connections_file_path": Path("cli_connections_file_path"),
                "connection_name": "cli_connection_name",
                "change_history_table": "cli_change_history_table",
                "create_change_history_table": False,
                "autocommit": False,
                "dry_run": False,
                "query_tag": "cli_query_tag",
            },
            id="Deploy: all cli, all yaml, all connection_kwargs",
        ),
        pytest.param(
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
                "connections_file_path": "cli_connections_file_path",
                "connection_name": "cli_connection_name",
                "change_history_table": "cli_change_history_table",
                "create_change_history_table": False,
                "autocommit": False,
                "dry_run": False,
                "query_tag": "cli_query_tag",
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
                "connections_file_path": "yaml_connections_file_path",
                "connection_name": "yaml_connection_name",
                "change_history_table": "yaml_change_history_table",
                "create_change_history_table": True,
                "autocommit": True,
                "dry_run": True,
                "query_tag": "yaml_query_tag",
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
                "connections_file_path": Path("cli_connections_file_path"),
                "connection_name": "cli_connection_name",
                "change_history_table": "cli_change_history_table",
                "create_change_history_table": False,
                "autocommit": False,
                "dry_run": False,
                "query_tag": "cli_query_tag",
            },
            id="Deploy: all env, all cli, all yaml, all connection_kwargs",
        ),
    ],
)
@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("pathlib.Path.is_file", return_value=True)
@mock.patch("schemachange.config.get_merged_config.parse_cli_args")
@mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs")
@mock.patch("schemachange.config.get_merged_config.DeployConfig.factory")
def test_get_merged_config_inheritance(
    mock_deploy_config_factory,
    mock_get_yaml_config_kwargs,
    mock_parse_cli_args,
    _,
    __,
    cli_kwargs,
    yaml_kwargs,
    expected,
):
    mock_parse_cli_args.return_value = {**cli_kwargs}
    mock_get_yaml_config_kwargs.return_value = {**yaml_kwargs}
    logger = structlog.testing.CapturingLogger()
    # noinspection PyTypeChecker
    get_merged_config(logger=logger)
    factory_kwargs = mock_deploy_config_factory.call_args.kwargs
    for actual_key, actual_value in factory_kwargs.items():
        assert expected[actual_key] == actual_value
        del expected[actual_key]
    assert len(expected.keys()) == 0


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
    [  # cli_args
        "schemachange",
        "--config-folder",
        str(assets_path),
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path / "schemachange-config.yml",
        "config_version": 1,
        "config_vars": {},
        "log_level": logging.INFO,
    },
    id="Deploy: Only required cli arguments",
)

param_full_cli_and_connection = pytest.param(
    [  # cli_args
        "schemachange",
        "--config-folder",
        str(assets_path),
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
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path / "schemachange-config.yml",
        "config_version": 1,
        "root_folder": "root-folder-from-cli",
        "modules_folder": "modules-folder-from-cli",
        "snowflake_account": "snowflake-account-from-cli",
        "snowflake_user": "snowflake-user-from-cli",
        "snowflake_role": "snowflake-role-from-cli",
        "snowflake_warehouse": "snowflake-warehouse-from-cli",
        "snowflake_database": "snowflake-database-from-cli",
        "snowflake_schema": "snowflake-schema-from-cli",
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
        "connection_name": "myaltconnection",
        "connections_file_path": assets_path / "alt-connections.toml",
    },
    id="Deploy: full cli and connections.toml",
)

param_full_yaml_no_connection = pytest.param(
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
                "change_history_table",
                "config_vars",
                "create_change_history_table",
                "autocommit",
                "dry_run",
                "query_tag",
            ]
        },
    },
    id="Deploy: yaml, no connections.toml",
)

param_full_yaml_and_connection = pytest.param(
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
                "change_history_table",
                "snowflake_private_key_path",
                "config_vars",
                "create_change_history_table",
                "autocommit",
                "dry_run",
                "query_tag",
                "connection_name",
            ]
        },
    },
    id="Deploy: full yaml and connections.toml",
)

param_full_yaml_and_connection_and_cli = pytest.param(
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
        "connection_name": "myaltconnection",
        "connections_file_path": assets_path / "alt-connections.toml",
    },
    id="Deploy: full yaml, connections.toml, and cli",
)

param_full_yaml_and_connection_and_cli_and_env = pytest.param(
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
        "--version-number-validation-regex",
        "version_number_validation_regex-from-cli",
        "--raise-exception-on-ignored-versioned-script",
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
        "connection_name": "myaltconnection",
        "connections_file_path": assets_path / "alt-connections.toml",
        "version_number_validation_regex-from-cli": "version_number_validation_regex-from-cli",
        "raise-exception-on-ignored-versioned-script": True

    },
    id="Deploy: full yaml, connections.toml, cli, and env",
)


param_connection_no_yaml = pytest.param(
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
        "config_vars": {},
        "log_level": logging.INFO,
    },
    id="Deploy: connections.toml, no yaml",
)

param_partial_yaml_and_connection = pytest.param(
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
        "log_level": logging.INFO,
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
                "connection_name",
            ]
        },
    },
    id="Deploy: partial yaml and connections.toml",
)


@pytest.mark.parametrize(
    "cli_args, expected",
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
@mock.patch("pathlib.Path.is_file", return_value=True)
@mock.patch("schemachange.config.get_merged_config.DeployConfig.factory")
def test_integration_get_merged_config_inheritance(
    mock_deploy_config_factory,
    _,
    __,
    cli_args,
    expected,
):
    logger = structlog.testing.CapturingLogger()
    with mock.patch("sys.argv", cli_args):
        # noinspection PyTypeChecker
        get_merged_config(logger=logger)
        factory_kwargs = mock_deploy_config_factory.call_args.kwargs
        for actual_key, actual_value in factory_kwargs.items():
            assert expected[actual_key] == actual_value
            del expected[actual_key]
        assert len(expected.keys()) == 0
