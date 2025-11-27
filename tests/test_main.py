from __future__ import annotations

import logging
import os
import tempfile
import unittest.mock as mock
from dataclasses import asdict
from pathlib import Path
from textwrap import dedent

import pytest

import schemachange.cli as cli
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import get_snowflake_identifier_string

assets_path = Path(__file__).parent / "config"

default_base_config = {
    # Shared configuration options
    "config_file_path": assets_path / "schemachange-config.yml",
    "root_folder": Path("."),
    "modules_folder": None,
    "config_vars": {},
}

default_deploy_config = {
    **default_base_config,
    # Deploy configuration options
    "snowflake_account": None,
    "snowflake_user": None,
    "snowflake_role": None,
    "snowflake_warehouse": None,
    "snowflake_database": None,
    "snowflake_schema": None,
    "connections_file_path": None,
    "connection_name": None,
    "change_history_table": ChangeHistoryTable(
        table_name="CHANGE_HISTORY",
        schema_name="SCHEMACHANGE",
        database_name="METADATA",
    ),
    "create_change_history_table": False,
    "autocommit": False,
    "dry_run": False,
    "query_tag": None,
    "version_number_validation_regex": None,
    "raise_exception_on_ignored_versioned_script": False,
}

required_args = [
    "--config-folder",
    str(assets_path),
    "--snowflake-account",
    "account",
    "--snowflake-user",
    "user",
    "--snowflake-warehouse",
    "warehouse",
    "--snowflake-role",
    "role",
]

required_config = {
    "config_file_path": assets_path / "schemachange-config.yml",
    "snowflake_account": "account",
    "snowflake_user": "user",
    "snowflake_warehouse": "warehouse",
    "snowflake_role": "role",
}
script_path = Path(__file__).parent.parent / "demo" / "basics_demo" / "2_test" / "A__basic001.sql"

no_command = pytest.param(
    "schemachange.cli.deploy",
    ["schemachange", *required_args],
    {**default_deploy_config, **required_config},
    None,
    id="no command",
)

deploy_only_required = pytest.param(
    "schemachange.cli.deploy",
    ["schemachange", "deploy", *required_args],
    {**default_deploy_config, **required_config},
    None,
    id="deploy: only required",
)

deploy_all_cli_arg_names = pytest.param(
    "schemachange.cli.deploy",
    [
        "schemachange",
        "deploy",
        "--config-folder",
        str(assets_path),
        "--config-file-name",
        "schemachange-config.yml",
        "--root-folder",
        str(assets_path),
        "--modules-folder",
        str(assets_path),
        "--vars",
        '{"var1": "from_cli", "var3": "also_from_cli"}',
        "--verbose",
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
        "db.schema.table_from_cli",
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
        "root_folder": assets_path,
        "modules_folder": assets_path,
        "snowflake_account": "snowflake-account-from-cli",
        "snowflake_user": "snowflake-user-from-cli",
        "snowflake_role": get_snowflake_identifier_string("snowflake-role-from-cli", "placeholder"),
        "snowflake_warehouse": get_snowflake_identifier_string("snowflake-warehouse-from-cli", "placeholder"),
        "snowflake_database": get_snowflake_identifier_string("snowflake-database-from-cli", "placeholder"),
        "snowflake_schema": get_snowflake_identifier_string("snowflake-schema-from-cli", "placeholder"),
        "change_history_table": ChangeHistoryTable(
            database_name="db",
            schema_name="schema",
            table_name="table_from_cli",
        ),
        "config_vars": {
            "var1": "from_cli",
            "var3": "also_from_cli",
        },
        "create_change_history_table": True,
        "autocommit": True,
        "log_level": logging.DEBUG,
        "dry_run": True,
        "query_tag": "query-tag-from-cli",
        "connection_name": "myaltconnection",
        "connections_file_path": assets_path / "alt-connections.toml",
    },
    None,
    id="deploy: all cli argument names",
)

deploy_all_cli_arg_flags = pytest.param(
    "schemachange.cli.deploy",
    [
        "schemachange",
        "deploy",
        "--config-folder",
        str(assets_path),
        "--config-file-name",
        "schemachange-config.yml",
        "-f",
        str(assets_path),
        "-m",
        str(assets_path),
        "--vars",
        '{"var1": "from_cli", "var3": "also_from_cli"}',
        "-v",
        "-a",
        "snowflake-account-from-cli",
        "-u",
        "snowflake-user-from-cli",
        "-r",
        "snowflake-role-from-cli",
        "-w",
        "snowflake-warehouse-from-cli",
        "-d",
        "snowflake-database-from-cli",
        "-s",
        "snowflake-schema-from-cli",
        "--connections-file-path",
        str(assets_path / "alt-connections.toml"),
        "--connection-name",
        "myaltconnection",
        "-c",
        "db.schema.table_from_cli",
        "--create-change-history-table",
        "-ac",
        "--dry-run",
        "--query-tag",
        "query-tag-from-cli",
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path / "schemachange-config.yml",
        "config_version": 1,
        "root_folder": assets_path,
        "modules_folder": assets_path,
        "snowflake_account": "snowflake-account-from-cli",
        "snowflake_user": "snowflake-user-from-cli",
        "snowflake_role": get_snowflake_identifier_string("snowflake-role-from-cli", "placeholder"),
        "snowflake_warehouse": get_snowflake_identifier_string("snowflake-warehouse-from-cli", "placeholder"),
        "snowflake_database": get_snowflake_identifier_string("snowflake-database-from-cli", "placeholder"),
        "snowflake_schema": get_snowflake_identifier_string("snowflake-schema-from-cli", "placeholder"),
        "change_history_table": ChangeHistoryTable(
            database_name="db",
            schema_name="schema",
            table_name="table_from_cli",
        ),
        "config_vars": {
            "var1": "from_cli",
            "var3": "also_from_cli",
        },
        "create_change_history_table": True,
        "autocommit": True,
        "log_level": logging.DEBUG,
        "dry_run": True,
        "query_tag": "query-tag-from-cli",
        "connection_name": "myaltconnection",
        "connections_file_path": assets_path / "alt-connections.toml",
    },
    None,
    id="deploy: all cli argument flags",
)

deploy_all_env_all_cli = pytest.param(
    "schemachange.cli.deploy",
    [
        "schemachange",
        "deploy",
        "--config-folder",
        str(assets_path),
        "--config-file-name",
        "schemachange-config.yml",
        "--root-folder",
        str(assets_path),
        "--modules-folder",
        str(assets_path),
        "--vars",
        '{"var1": "from_cli", "var3": "also_from_cli"}',
        "--verbose",
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
        "db.schema.table_from_cli",
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
        "root_folder": assets_path,
        "modules_folder": assets_path,
        "snowflake_account": "snowflake-account-from-cli",
        "snowflake_user": "snowflake-user-from-cli",
        "snowflake_role": get_snowflake_identifier_string("snowflake-role-from-cli", "placeholder"),
        "snowflake_warehouse": get_snowflake_identifier_string("snowflake-warehouse-from-cli", "placeholder"),
        "snowflake_database": get_snowflake_identifier_string("snowflake-database-from-cli", "placeholder"),
        "snowflake_schema": get_snowflake_identifier_string("snowflake-schema-from-cli", "placeholder"),
        "change_history_table": ChangeHistoryTable(
            database_name="db",
            schema_name="schema",
            table_name="table_from_cli",
        ),
        "config_vars": {
            "var1": "from_cli",
            "var3": "also_from_cli",
        },
        "create_change_history_table": True,
        "autocommit": True,
        "log_level": logging.DEBUG,
        "dry_run": True,
        "query_tag": "query-tag-from-cli",
        "connection_name": "myaltconnection",
        "connections_file_path": assets_path / "alt-connections.toml",
    },
    None,
    id="deploy: all env_vars and all cli argument names",
)

deploy_snowflake_oauth_env_var = pytest.param(
    "schemachange.cli.deploy",
    [
        "schemachange",
        "deploy",
        *required_args,
    ],
    {
        **default_deploy_config,
        "snowflake_account": "account",
        "snowflake_user": "user",
        "snowflake_warehouse": "warehouse",
        "snowflake_role": "role",
    },
    None,
    id="deploy: oauth env var",
)

deploy_snowflake_oauth_file = pytest.param(
    "schemachange.cli.deploy",
    [
        "schemachange",
        "deploy",
        *required_args,
    ],
    {
        **default_deploy_config,
        "snowflake_account": "account",
        "snowflake_user": "user",
        "snowflake_warehouse": "warehouse",
        "snowflake_role": "role",
    },
    None,
    id="deploy: oauth file",
)

render_only_required = pytest.param(
    "schemachange.cli.render",
    [
        "schemachange",
        "render",
        str(script_path),
        "--config-folder",
        str(assets_path),
    ],
    {**default_base_config},
    script_path,
    id="render: only required",
)

render_all_cli_arg_names = pytest.param(
    "schemachange.cli.render",
    [
        "schemachange",
        "render",
        "--root-folder",
        ".",
        "--vars",
        '{"var1": "val"}',
        "--verbose",
        str(script_path),
        "--config-folder",
        str(assets_path),
    ],
    {
        **default_base_config,
        "root_folder": Path("."),
        "config_vars": {"var1": "val"},
        "log_level": logging.DEBUG,
    },
    script_path,
    id="render: all cli argument names",
)


@pytest.mark.parametrize(
    "to_mock, cli_args, expected_config, expected_script_path",
    [
        no_command,
        deploy_only_required,
        deploy_all_cli_arg_names,
        deploy_all_cli_arg_flags,
        deploy_all_env_all_cli,
        deploy_snowflake_oauth_env_var,
        deploy_snowflake_oauth_file,
        render_only_required,
        render_all_cli_arg_names,
    ],
)
@mock.patch("pathlib.Path.is_file", return_value=True)
@mock.patch("snowflake.connector.connect")
@mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string")
def test_main_deploy_subcommand_given_arguments_make_sure_arguments_set_on_call(
    mock_id_string,
    mock_connect,
    _,
    to_mock: str,
    cli_args: list[str],
    expected_config: dict,
    expected_script_path: Path | None,
):
    # Mock snowflake connection
    mock_conn = mock.Mock()
    mock_conn.account = "test_account"
    mock_conn.user = "test_user"
    mock_conn.role = "test_role"
    mock_conn.warehouse = "test_warehouse"
    mock_conn.database = "test_db"
    mock_conn.schema = "test_schema"
    mock_conn.session_id = "test_session_123"
    mock_connect.return_value = mock_conn

    # Mock get_snowflake_identifier_string to return the value as-is
    mock_id_string.side_effect = lambda val, _: val

    # Clear environment variables to prevent leakage from GitHub Actions
    with mock.patch.dict(os.environ, {}, clear=True):
        with mock.patch("sys.argv", cli_args):
            with mock.patch(to_mock) as mock_command:
                cli.main()
                mock_command.assert_called_once()
                _, call_kwargs = mock_command.call_args
                for expected_arg, expected_value in expected_config.items():
                    actual_value = getattr(call_kwargs["config"], expected_arg)
                    if hasattr(actual_value, "table_name"):
                        assert asdict(actual_value) == asdict(expected_value)
                    else:
                        assert actual_value == expected_value
                if expected_script_path is not None:
                    assert call_kwargs["script_path"] == expected_script_path


@pytest.mark.parametrize(
    "to_mock, args,  expected_config, expected_script_path",
    [
        (
            "schemachange.cli.deploy",
            [
                "schemachange",
                "deploy",
                "--config-folder",
                "DUMMY",
            ],
            {
                **default_deploy_config,
                "snowflake_user": "user",
                "snowflake_warehouse": "warehouse",
                "snowflake_role": "role",
                "snowflake_account": "account",
            },
            None,
        ),
        (
            "schemachange.cli.render",
            [
                "schemachange",
                "render",
                str(script_path),
                "--config-folder",
                "DUMMY",
            ],
            default_base_config,
            script_path,
        ),
    ],
)
@mock.patch("snowflake.connector.connect")
@mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string")
def test_main_deploy_config_folder(
    mock_id_string,
    mock_connect,
    to_mock: str,
    args: list[str],
    expected_config: dict,
    expected_script_path: Path | None,
):
    # Mock snowflake connection
    mock_conn = mock.Mock()
    mock_conn.account = "test_account"
    mock_conn.user = "test_user"
    mock_conn.role = "test_role"
    mock_conn.warehouse = "test_warehouse"
    mock_conn.database = "test_db"
    mock_conn.schema = "test_schema"
    mock_conn.session_id = "test_session_123"
    mock_connect.return_value = mock_conn

    # Mock get_snowflake_identifier_string to return the value as-is
    mock_id_string.side_effect = lambda val, _: val

    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "schemachange-config.yml"), "w") as f:
            f.write(
                dedent(
                    """
                    snowflake_account: account
                    snowflake_user: user
                    snowflake_warehouse: warehouse
                    snowflake_role: role
                    """
                )
            )

        # noinspection PyTypeChecker
        args[args.index("DUMMY")] = d
        expected_config["config_file_path"] = Path(d) / "schemachange-config.yml"

        # Clear environment variables to prevent leakage from GitHub Actions
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch(to_mock) as mock_command:
                with mock.patch("sys.argv", args):
                    cli.main()
                    mock_command.assert_called_once()
                    _, call_kwargs = mock_command.call_args
                    for expected_arg, expected_value in expected_config.items():
                        actual_value = getattr(call_kwargs["config"], expected_arg)
                        if hasattr(actual_value, "table_name"):
                            assert asdict(actual_value) == asdict(expected_value)
                        else:
                            assert actual_value == expected_value
                    if expected_script_path is not None:
                        assert call_kwargs["script_path"] == expected_script_path


@pytest.mark.parametrize(
    "to_mock, args, expected_config, expected_script_path",
    [
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", *required_args, "--modules-folder", "DUMMY"],
            {**default_deploy_config, **required_config, "modules_folder": "DUMMY"},
            None,
        ),
        (
            "schemachange.cli.render",
            [
                "schemachange",
                "render",
                str(script_path),
                "--modules-folder",
                "DUMMY",
                "--config-folder",
                str(assets_path),
            ],
            {**default_base_config, "modules_folder": "DUMMY"},
            script_path,
        ),
    ],
)
@mock.patch("snowflake.connector.connect")
@mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string")
def test_main_deploy_modules_folder(
    mock_id_string,
    mock_connect,
    to_mock: str,
    args: list[str],
    expected_config: dict,
    expected_script_path: Path | None,
):
    # Mock snowflake connection
    mock_conn = mock.Mock()
    mock_conn.account = "test_account"
    mock_conn.user = "test_user"
    mock_conn.role = "test_role"
    mock_conn.warehouse = "test_warehouse"
    mock_conn.database = "test_db"
    mock_conn.schema = "test_schema"
    mock_conn.session_id = "test_session_123"
    mock_connect.return_value = mock_conn

    # Mock get_snowflake_identifier_string to return the value as-is
    mock_id_string.side_effect = lambda val, _: val

    with tempfile.TemporaryDirectory() as d:
        # noinspection PyTypeChecker
        args[args.index("DUMMY")] = d
        expected_config["modules_folder"] = Path(d)

        # Clear environment variables to prevent leakage from GitHub Actions
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch(to_mock) as mock_command:
                with mock.patch("sys.argv", args):
                    cli.main()
                    mock_command.assert_called_once()
                    _, call_kwargs = mock_command.call_args
                    for expected_arg, expected_value in expected_config.items():
                        actual_value = getattr(call_kwargs["config"], expected_arg)
                        if hasattr(actual_value, "table_name"):
                            assert asdict(actual_value) == asdict(expected_value)
                        else:
                            assert actual_value == expected_value
                    if expected_script_path is not None:
                        assert call_kwargs["script_path"] == expected_script_path
