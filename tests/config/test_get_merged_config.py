import logging
import os

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
        "version_number_validation_regex": "version_number_validation_regex-from-cli",
        "raise_exception_on_ignored_versioned_script": True,
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


# ============================================================================
# Priority Order Integration Tests: ENV Variable Layer
# ============================================================================
# These tests verify that the configuration priority order works correctly:
# Priority: CLI > ENV > YAML > connections.toml


@pytest.mark.parametrize(
    "env_vars, yaml_kwargs, expected",
    [
        pytest.param(
            # env_vars
            {
                "SNOWFLAKE_ACCOUNT": "env_snowflake_account",
                "SNOWFLAKE_USER": "env_snowflake_user",
                "SNOWFLAKE_ROLE": "env_snowflake_role",
                "SNOWFLAKE_WAREHOUSE": "env_snowflake_warehouse",
                "SNOWFLAKE_DATABASE": "env_snowflake_database",
                "SNOWFLAKE_SCHEMA": "env_snowflake_schema",
            },
            # yaml_kwargs
            {
                "root_folder": "yaml_root_folder",
                "snowflake_account": "yaml_snowflake_account",
                "snowflake_user": "yaml_snowflake_user",
                "snowflake_role": "yaml_snowflake_role",
                "snowflake_warehouse": "yaml_snowflake_warehouse",
                "snowflake_database": "yaml_snowflake_database",
                "snowflake_schema": "yaml_snowflake_schema",
            },
            # expected (ENV should override YAML)
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "root_folder": "yaml_root_folder",  # YAML (not in ENV)
                "snowflake_account": "env_snowflake_account",  # ENV overrides YAML
                "snowflake_user": "env_snowflake_user",  # ENV overrides YAML
                "snowflake_role": "env_snowflake_role",  # ENV overrides YAML
                "snowflake_warehouse": "env_snowflake_warehouse",  # ENV overrides YAML
                "snowflake_database": "env_snowflake_database",  # ENV overrides YAML
                "snowflake_schema": "env_snowflake_schema",  # ENV overrides YAML
            },
            id="ENV overrides YAML: connection parameters",
        ),
        pytest.param(
            # env_vars (partial - only some parameters)
            {
                "SNOWFLAKE_ACCOUNT": "env_snowflake_account",
                "SNOWFLAKE_WAREHOUSE": "env_snowflake_warehouse",
            },
            # yaml_kwargs
            {
                "snowflake_account": "yaml_snowflake_account",
                "snowflake_user": "yaml_snowflake_user",
                "snowflake_role": "yaml_snowflake_role",
                "snowflake_warehouse": "yaml_snowflake_warehouse",
                "snowflake_database": "yaml_snowflake_database",
                "snowflake_schema": "yaml_snowflake_schema",
            },
            # expected (ENV overrides where set, YAML provides rest)
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "snowflake_account": "env_snowflake_account",  # ENV overrides YAML
                "snowflake_user": "yaml_snowflake_user",  # From YAML
                "snowflake_role": "yaml_snowflake_role",  # From YAML
                "snowflake_warehouse": "env_snowflake_warehouse",  # ENV overrides YAML
                "snowflake_database": "yaml_snowflake_database",  # From YAML
                "snowflake_schema": "yaml_snowflake_schema",  # From YAML
            },
            id="ENV overrides YAML: partial ENV vars",
        ),
        pytest.param(
            # env_vars (only ENV, no YAML)
            {
                "SNOWFLAKE_ACCOUNT": "env_snowflake_account",
                "SNOWFLAKE_USER": "env_snowflake_user",
                "SNOWFLAKE_ROLE": "env_snowflake_role",
            },
            # yaml_kwargs (empty)
            {},
            # expected
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "snowflake_account": "env_snowflake_account",
                "snowflake_user": "env_snowflake_user",
                "snowflake_role": "env_snowflake_role",
            },
            id="ENV only: no YAML config",
        ),
        pytest.param(
            # env_vars (authentication parameters)
            {
                "SNOWFLAKE_ACCOUNT": "env_snowflake_account",
                "SNOWFLAKE_USER": "env_snowflake_user",
                "SNOWFLAKE_AUTHENTICATOR": "snowflake_jwt",
                "SNOWFLAKE_PRIVATE_KEY_PATH": "/env/path/to/key.pem",
            },
            # yaml_kwargs
            {
                "snowflake_account": "yaml_snowflake_account",
                "snowflake_user": "yaml_snowflake_user",
                "authenticator": "password",
                "private_key_path": "/yaml/path/to/key.pem",
            },
            # expected (ENV should override YAML for auth params too)
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "snowflake_account": "env_snowflake_account",
                "snowflake_user": "env_snowflake_user",
                "authenticator": "snowflake_jwt",  # ENV overrides YAML
                "private_key_path": "/env/path/to/key.pem",  # ENV overrides YAML
            },
            id="ENV overrides YAML: authentication parameters",
        ),
        pytest.param(
            # env_vars (connections file path)
            {
                "SNOWFLAKE_CONNECTIONS_FILE_PATH": "/env/connections.toml",
                "SNOWFLAKE_DEFAULT_CONNECTION_NAME": "env_connection",
            },
            # yaml_kwargs
            {
                "connections_file_path": "/yaml/connections.toml",
                "connection_name": "yaml_connection",
            },
            # expected
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "connections_file_path": Path("/env/connections.toml"),
                "connection_name": "env_connection",
            },
            id="ENV overrides YAML: connections file path and connection name",
        ),
    ],
)
@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("pathlib.Path.is_file", return_value=True)
@mock.patch("schemachange.config.get_merged_config.parse_cli_args")
@mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs")
@mock.patch("schemachange.config.get_merged_config.DeployConfig.factory")
def test_priority_env_overrides_yaml(
    mock_deploy_config_factory,
    mock_get_yaml_config_kwargs,
    mock_parse_cli_args,
    _,
    __,
    env_vars,
    yaml_kwargs,
    expected,
):
    """Test that ENV variables override YAML configuration (no CLI args)."""
    # Setup CLI with minimal required args only
    cli_kwargs = {**default_cli_kwargs}
    mock_parse_cli_args.return_value = cli_kwargs
    mock_get_yaml_config_kwargs.return_value = yaml_kwargs

    logger = structlog.testing.CapturingLogger()

    with mock.patch.dict(os.environ, env_vars, clear=True):
        # noinspection PyTypeChecker
        get_merged_config(logger=logger)

    factory_kwargs = mock_deploy_config_factory.call_args.kwargs
    for actual_key, actual_value in factory_kwargs.items():
        assert expected[actual_key] == actual_value
        del expected[actual_key]
    assert len(expected.keys()) == 0


@pytest.mark.parametrize(
    "env_vars, cli_kwargs, yaml_kwargs, expected",
    [
        pytest.param(
            # env_vars
            {
                "SNOWFLAKE_ACCOUNT": "env_snowflake_account",
                "SNOWFLAKE_USER": "env_snowflake_user",
                "SNOWFLAKE_ROLE": "env_snowflake_role",
                "SNOWFLAKE_WAREHOUSE": "env_snowflake_warehouse",
            },
            # cli_kwargs
            {
                **default_cli_kwargs,
                "snowflake_account": "cli_snowflake_account",
                "snowflake_user": "cli_snowflake_user",
            },
            # yaml_kwargs
            {
                "snowflake_account": "yaml_snowflake_account",
                "snowflake_user": "yaml_snowflake_user",
                "snowflake_role": "yaml_snowflake_role",
                "snowflake_warehouse": "yaml_snowflake_warehouse",
                "snowflake_database": "yaml_snowflake_database",
            },
            # expected (CLI > ENV > YAML)
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "snowflake_account": "cli_snowflake_account",  # CLI wins
                "snowflake_user": "cli_snowflake_user",  # CLI wins
                "snowflake_role": "env_snowflake_role",  # ENV overrides YAML
                "snowflake_warehouse": "env_snowflake_warehouse",  # ENV overrides YAML
                "snowflake_database": "yaml_snowflake_database",  # From YAML
            },
            id="CLI overrides ENV overrides YAML: connection parameters",
        ),
        pytest.param(
            # env_vars
            {
                "SNOWFLAKE_ACCOUNT": "env_snowflake_account",
                "SNOWFLAKE_ROLE": "env_snowflake_role",
                "SNOWFLAKE_WAREHOUSE": "env_snowflake_warehouse",
            },
            # cli_kwargs
            {
                **default_cli_kwargs,
                "snowflake_warehouse": "cli_snowflake_warehouse",
            },
            # yaml_kwargs
            {
                "snowflake_account": "yaml_snowflake_account",
                "snowflake_role": "yaml_snowflake_role",
                "snowflake_warehouse": "yaml_snowflake_warehouse",
                "root_folder": "yaml_root_folder",
            },
            # expected (CLI > ENV > YAML)
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "snowflake_account": "env_snowflake_account",  # ENV overrides YAML
                "snowflake_role": "env_snowflake_role",  # ENV overrides YAML
                "snowflake_warehouse": "cli_snowflake_warehouse",  # CLI overrides ENV
                "root_folder": "yaml_root_folder",  # From YAML
            },
            id="CLI overrides ENV: single parameter",
        ),
        pytest.param(
            # env_vars (all connection params)
            {
                "SNOWFLAKE_ACCOUNT": "env_snowflake_account",
                "SNOWFLAKE_USER": "env_snowflake_user",
                "SNOWFLAKE_ROLE": "env_snowflake_role",
                "SNOWFLAKE_WAREHOUSE": "env_snowflake_warehouse",
                "SNOWFLAKE_DATABASE": "env_snowflake_database",
                "SNOWFLAKE_SCHEMA": "env_snowflake_schema",
            },
            # cli_kwargs (all connection params)
            {
                **default_cli_kwargs,
                "snowflake_account": "cli_snowflake_account",
                "snowflake_user": "cli_snowflake_user",
                "snowflake_role": "cli_snowflake_role",
                "snowflake_warehouse": "cli_snowflake_warehouse",
                "snowflake_database": "cli_snowflake_database",
                "snowflake_schema": "cli_snowflake_schema",
            },
            # yaml_kwargs
            {
                "snowflake_account": "yaml_snowflake_account",
                "snowflake_user": "yaml_snowflake_user",
                "snowflake_role": "yaml_snowflake_role",
                "snowflake_warehouse": "yaml_snowflake_warehouse",
                "snowflake_database": "yaml_snowflake_database",
                "snowflake_schema": "yaml_snowflake_schema",
            },
            # expected (CLI should win for all)
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "snowflake_account": "cli_snowflake_account",
                "snowflake_user": "cli_snowflake_user",
                "snowflake_role": "cli_snowflake_role",
                "snowflake_warehouse": "cli_snowflake_warehouse",
                "snowflake_database": "cli_snowflake_database",
                "snowflake_schema": "cli_snowflake_schema",
            },
            id="CLI overrides ENV and YAML: all connection parameters",
        ),
        pytest.param(
            # env_vars (authentication parameters)
            {
                "SNOWFLAKE_AUTHENTICATOR": "env_authenticator",
                "SNOWFLAKE_PRIVATE_KEY_PATH": "/env/key.pem",
                "SNOWFLAKE_CONNECTIONS_FILE_PATH": "/env/connections.toml",
            },
            # cli_kwargs (CLI overrides authenticator only)
            {
                **default_cli_kwargs,
                "authenticator": "cli_authenticator",
            },
            # yaml_kwargs
            {
                "authenticator": "yaml_authenticator",
                "private_key_path": "/yaml/key.pem",
                "connections_file_path": "/yaml/connections.toml",
            },
            # expected
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "authenticator": "cli_authenticator",  # CLI wins
                "private_key_path": "/env/key.pem",  # ENV overrides YAML
                "connections_file_path": Path(
                    "/env/connections.toml"
                ),  # ENV overrides YAML
            },
            id="CLI overrides ENV overrides YAML: authentication parameters",
        ),
    ],
)
@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("pathlib.Path.is_file", return_value=True)
@mock.patch("schemachange.config.get_merged_config.parse_cli_args")
@mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs")
@mock.patch("schemachange.config.get_merged_config.DeployConfig.factory")
def test_priority_cli_overrides_env_overrides_yaml(
    mock_deploy_config_factory,
    mock_get_yaml_config_kwargs,
    mock_parse_cli_args,
    _,
    __,
    env_vars,
    cli_kwargs,
    yaml_kwargs,
    expected,
):
    """Test that CLI args override ENV vars, which override YAML configuration."""
    mock_parse_cli_args.return_value = cli_kwargs
    mock_get_yaml_config_kwargs.return_value = yaml_kwargs

    logger = structlog.testing.CapturingLogger()

    with mock.patch.dict(os.environ, env_vars, clear=True):
        # noinspection PyTypeChecker
        get_merged_config(logger=logger)

    factory_kwargs = mock_deploy_config_factory.call_args.kwargs
    for actual_key, actual_value in factory_kwargs.items():
        assert expected[actual_key] == actual_value
        del expected[actual_key]
    assert len(expected.keys()) == 0


@pytest.mark.parametrize(
    "env_vars, expected_auth_params",
    [
        pytest.param(
            {
                "SNOWFLAKE_AUTHENTICATOR": "snowflake_jwt",
                "SNOWFLAKE_PRIVATE_KEY_PATH": "/path/to/private_key.pem",
            },
            {
                "authenticator": "snowflake_jwt",
                "private_key_path": "/path/to/private_key.pem",
            },
            id="Authentication: JWT with private key",
        ),
        pytest.param(
            {
                "SNOWFLAKE_AUTHENTICATOR": "snowflake_jwt",
                "SNOWFLAKE_PRIVATE_KEY_PATH": "/path/to/private_key.pem",
                "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": "secret_passphrase",
            },
            {
                "authenticator": "snowflake_jwt",
                "private_key_path": "/path/to/private_key.pem",
                "private_key_passphrase": "secret_passphrase",
            },
            id="Authentication: JWT with encrypted private key",
        ),
        pytest.param(
            {
                "SNOWFLAKE_AUTHENTICATOR": "oauth",
                "SNOWFLAKE_TOKEN_FILE_PATH": "/path/to/token.txt",
            },
            {
                "authenticator": "oauth",
                "token_file_path": "/path/to/token.txt",
            },
            id="Authentication: OAuth with token file",
        ),
        pytest.param(
            {
                "SNOWFLAKE_AUTHENTICATOR": "externalbrowser",
            },
            {
                "authenticator": "externalbrowser",
            },
            id="Authentication: External browser",
        ),
        pytest.param(
            {
                "SNOWFLAKE_PRIVATE_KEY_PATH": "/path/to/key.pem",
            },
            {
                "private_key_path": "/path/to/key.pem",
            },
            id="Authentication: Private key path only",
        ),
    ],
)
@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("pathlib.Path.is_file", return_value=True)
@mock.patch("schemachange.config.get_merged_config.parse_cli_args")
@mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs")
@mock.patch("schemachange.config.get_merged_config.DeployConfig.factory")
def test_priority_env_authentication_parameters(
    mock_deploy_config_factory,
    mock_get_yaml_config_kwargs,
    mock_parse_cli_args,
    _,
    __,
    env_vars,
    expected_auth_params,
):
    """Test that authentication parameters from ENV vars are correctly passed through."""
    cli_kwargs = {**default_cli_kwargs}
    mock_parse_cli_args.return_value = cli_kwargs
    mock_get_yaml_config_kwargs.return_value = {}

    logger = structlog.testing.CapturingLogger()

    with mock.patch.dict(os.environ, env_vars, clear=True):
        # noinspection PyTypeChecker
        get_merged_config(logger=logger)

    factory_kwargs = mock_deploy_config_factory.call_args.kwargs

    # Verify authentication parameters are present
    for key, expected_value in expected_auth_params.items():
        assert (
            key in factory_kwargs
        ), f"Expected key '{key}' not found in factory_kwargs"  # noqa: E713
        assert (
            factory_kwargs[key] == expected_value
        ), f"Expected {key}={expected_value}, got {factory_kwargs[key]}"


@pytest.mark.parametrize(
    "env_vars, yaml_kwargs, expected_has_param",
    [
        pytest.param(
            # Empty string ENV var should not override YAML
            {"SNOWFLAKE_ACCOUNT": ""},
            {"snowflake_account": "yaml_account"},
            {"snowflake_account": "yaml_account"},
            id="Empty ENV var does not override YAML",
        ),
        pytest.param(
            # No ENV vars
            {},
            {"snowflake_account": "yaml_account", "snowflake_user": "yaml_user"},
            {"snowflake_account": "yaml_account", "snowflake_user": "yaml_user"},
            id="No ENV vars: YAML values used",
        ),
        pytest.param(
            # Mixed: some empty, some with values
            {
                "SNOWFLAKE_ACCOUNT": "env_account",
                "SNOWFLAKE_USER": "",  # Empty should not override
            },
            {
                "snowflake_account": "yaml_account",
                "snowflake_user": "yaml_user",
            },
            {
                "snowflake_account": "env_account",
                "snowflake_user": "yaml_user",
            },
            id="Mixed ENV vars: only non-empty override",
        ),
    ],
)
@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("pathlib.Path.is_file", return_value=True)
@mock.patch("schemachange.config.get_merged_config.parse_cli_args")
@mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs")
@mock.patch("schemachange.config.get_merged_config.DeployConfig.factory")
def test_priority_env_edge_cases(
    mock_deploy_config_factory,
    mock_get_yaml_config_kwargs,
    mock_parse_cli_args,
    _,
    __,
    env_vars,
    yaml_kwargs,
    expected_has_param,
):
    """Test edge cases with empty ENV vars and None values."""
    cli_kwargs = {**default_cli_kwargs}
    mock_parse_cli_args.return_value = cli_kwargs
    mock_get_yaml_config_kwargs.return_value = yaml_kwargs

    logger = structlog.testing.CapturingLogger()

    with mock.patch.dict(os.environ, env_vars, clear=True):
        # noinspection PyTypeChecker
        get_merged_config(logger=logger)

    factory_kwargs = mock_deploy_config_factory.call_args.kwargs

    # Verify expected parameters
    for key, expected_value in expected_has_param.items():
        assert (
            factory_kwargs.get(key) == expected_value
        ), f"Expected {key}={expected_value}, got {factory_kwargs.get(key)}"


@pytest.mark.parametrize(
    "env_vars, cli_kwargs, yaml_kwargs, expected",
    [
        pytest.param(
            # env_vars (connection params)
            {
                "SNOWFLAKE_ACCOUNT": "env_account",
                "SNOWFLAKE_USER": "env_user",
                "SNOWFLAKE_ROLE": "env_role",
                "SNOWFLAKE_WAREHOUSE": "env_warehouse",
                "SNOWFLAKE_DATABASE": "env_database",
                "SNOWFLAKE_SCHEMA": "env_schema",
            },
            # cli_kwargs (override some, plus connection file)
            {
                **default_cli_kwargs,
                "snowflake_account": "cli_account",
                "connections_file_path": "/cli/connections.toml",
                "connection_name": "cli_connection",
            },
            # yaml_kwargs (base config, lowest priority for connection params)
            {
                "snowflake_account": "yaml_account",
                "snowflake_user": "yaml_user",
                "snowflake_role": "yaml_role",
                "snowflake_warehouse": "yaml_warehouse",
                "snowflake_database": "yaml_database",
                "snowflake_schema": "yaml_schema",
                "connections_file_path": "/yaml/connections.toml",
                "connection_name": "yaml_connection",
                "root_folder": "yaml_root_folder",
            },
            # expected: CLI > ENV > YAML > connections.toml
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                # CLI wins for these
                "snowflake_account": "cli_account",
                "connections_file_path": Path("/cli/connections.toml"),
                "connection_name": "cli_connection",
                # ENV wins for these (CLI didn't specify)
                "snowflake_user": "env_user",
                "snowflake_role": "env_role",
                "snowflake_warehouse": "env_warehouse",
                "snowflake_database": "env_database",
                "snowflake_schema": "env_schema",
                # YAML wins for these (not in CLI or ENV)
                "root_folder": "yaml_root_folder",
            },
            id="All 4 layers: CLI > ENV > YAML > connections.toml",
        ),
        pytest.param(
            # env_vars (partial)
            {
                "SNOWFLAKE_WAREHOUSE": "env_warehouse",
                "SNOWFLAKE_AUTHENTICATOR": "snowflake_jwt",
                "SNOWFLAKE_PRIVATE_KEY_PATH": "/env/key.pem",
            },
            # cli_kwargs (partial)
            {
                **default_cli_kwargs,
                "snowflake_role": "cli_role",
                "dry_run": True,
            },
            # yaml_kwargs (partial)
            {
                "snowflake_account": "yaml_account",
                "snowflake_user": "yaml_user",
                "snowflake_role": "yaml_role",
                "snowflake_warehouse": "yaml_warehouse",
                "authenticator": "password",
                "connection_name": "yaml_connection",
            },
            # expected
            {
                "config_file_path": Path("schemachange-config.yml"),
                "config_vars": {},
                "subcommand": "deploy",
                "snowflake_role": "cli_role",  # CLI
                "dry_run": True,  # CLI
                "snowflake_warehouse": "env_warehouse",  # ENV > YAML
                "authenticator": "snowflake_jwt",  # ENV > YAML
                "private_key_path": "/env/key.pem",  # ENV
                "snowflake_account": "yaml_account",  # YAML
                "snowflake_user": "yaml_user",  # YAML
                "connection_name": "yaml_connection",  # YAML
            },
            id="All 4 layers: partial configs from each layer",
        ),
    ],
)
@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("pathlib.Path.is_file", return_value=True)
@mock.patch("schemachange.config.get_merged_config.parse_cli_args")
@mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs")
@mock.patch("schemachange.config.get_merged_config.DeployConfig.factory")
def test_priority_all_four_layers(
    mock_deploy_config_factory,
    mock_get_yaml_config_kwargs,
    mock_parse_cli_args,
    _,
    __,
    env_vars,
    cli_kwargs,
    yaml_kwargs,
    expected,
):
    """Test all 4 configuration layers working together: CLI > ENV > YAML > connections.toml."""
    mock_parse_cli_args.return_value = cli_kwargs
    mock_get_yaml_config_kwargs.return_value = yaml_kwargs

    logger = structlog.testing.CapturingLogger()

    with mock.patch.dict(os.environ, env_vars, clear=True):
        # noinspection PyTypeChecker
        get_merged_config(logger=logger)

    factory_kwargs = mock_deploy_config_factory.call_args.kwargs
    for actual_key, actual_value in factory_kwargs.items():
        assert (
            expected[actual_key] == actual_value
        ), f"Mismatch for {actual_key}: expected {expected[actual_key]}, got {actual_value}"
        del expected[actual_key]
    assert len(expected.keys()) == 0
