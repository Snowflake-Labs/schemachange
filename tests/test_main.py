from __future__ import annotations

import json
import logging
import os
import tomlkit
import tempfile
import unittest.mock as mock
from dataclasses import asdict
from pathlib import Path
from textwrap import dedent

import pytest
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable

import schemachange.cli as cli
from schemachange.config.utils import get_snowflake_identifier_string

assets_path = Path(__file__).parent / "config"


def get_connection_from_toml(file_path: Path, connection_name: str) -> dict:
    with file_path.open("rb") as f:
        connections = tomlkit.load(f)
        return connections[connection_name]


alt_connection = get_connection_from_toml(
    file_path=assets_path / "alt-connections.toml",
    connection_name="myaltconnection",
)
default_base_config = {
    # Shared configuration options
    "config_file_path": Path(".") / "schemachange-config.yml",
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
    "snowflake_authenticator": "snowflake",
    "snowflake_password": None,
    "snowflake_oauth_token": None,
    "snowflake_private_key_path": None,
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
}

required_args = [
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
    "snowflake_account": "account",
    "snowflake_user": "user",
    "snowflake_warehouse": "warehouse",
    "snowflake_role": "role",
    "snowflake_password": "password",
}
script_path = Path(__file__).parent.parent / "demo" / "basics_demo" / "A__basic001.sql"

no_command = pytest.param(
    "schemachange.cli.deploy",
    {"SNOWFLAKE_PASSWORD": "password"},
    ["schemachange", *required_args],
    {**default_deploy_config, **required_config},
    None,
    id="no command",
)

deploy_only_required = pytest.param(
    "schemachange.cli.deploy",
    {"SNOWFLAKE_PASSWORD": "password"},
    ["schemachange", "deploy", *required_args],
    {**default_deploy_config, **required_config},
    None,
    id="deploy: only required",
)

deploy_all_cli_arg_names = pytest.param(
    "schemachange.cli.deploy",
    {},
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
        "--snowflake-authenticator",
        "externalbrowser",
        "--snowflake-private-key-path",
        str(assets_path / "private_key.txt"),
        "--snowflake-token-path",
        str(assets_path / "oauth_token_path.txt"),
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
        "--oauth-config",
        json.dumps({"oauth_config_variable": "cli_oauth_config_value"}),
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path / "schemachange-config.yml",
        "config_version": 1,
        "root_folder": assets_path,
        "modules_folder": assets_path,
        "snowflake_account": "snowflake-account-from-cli",
        "snowflake_user": "snowflake-user-from-cli",
        "snowflake_role": get_snowflake_identifier_string(
            "snowflake-role-from-cli", "placeholder"
        ),
        "snowflake_warehouse": get_snowflake_identifier_string(
            "snowflake-warehouse-from-cli", "placeholder"
        ),
        "snowflake_database": get_snowflake_identifier_string(
            "snowflake-database-from-cli", "placeholder"
        ),
        "snowflake_schema": get_snowflake_identifier_string(
            "snowflake-schema-from-cli", "placeholder"
        ),
        "snowflake_authenticator": "externalbrowser",
        "snowflake_private_key_path": assets_path / "private_key.txt",
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
        "snowflake_password": alt_connection["password"],
    },
    None,
    id="deploy: all cli argument names",
)

deploy_all_cli_arg_flags = pytest.param(
    "schemachange.cli.deploy",
    {},
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
        "-A",
        "externalbrowser",
        "-k",
        str(assets_path / "private_key.txt"),
        "-t",
        str(assets_path / "oauth_token_path.txt"),
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
        "--oauth-config",
        json.dumps({"oauth_config_variable": "cli_oauth_config_value"}),
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path / "schemachange-config.yml",
        "config_version": 1,
        "root_folder": assets_path,
        "modules_folder": assets_path,
        "snowflake_account": "snowflake-account-from-cli",
        "snowflake_user": "snowflake-user-from-cli",
        "snowflake_role": get_snowflake_identifier_string(
            "snowflake-role-from-cli", "placeholder"
        ),
        "snowflake_warehouse": get_snowflake_identifier_string(
            "snowflake-warehouse-from-cli", "placeholder"
        ),
        "snowflake_database": get_snowflake_identifier_string(
            "snowflake-database-from-cli", "placeholder"
        ),
        "snowflake_schema": get_snowflake_identifier_string(
            "snowflake-schema-from-cli", "placeholder"
        ),
        "snowflake_authenticator": "externalbrowser",
        "snowflake_private_key_path": assets_path / "private_key.txt",
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
        "snowflake_password": alt_connection["password"],
    },
    None,
    id="deploy: all cli argument flags",
)

deploy_all_env_all_cli = pytest.param(
    "schemachange.cli.deploy",
    {
        "SNOWFLAKE_PASSWORD": "env_snowflake_password",
        "SNOWFLAKE_PRIVATE_KEY_PATH": str(assets_path / "alt_private_key.txt"),
        "SNOWFLAKE_AUTHENTICATOR": "snowflake_jwt",
        "SNOWFLAKE_TOKEN": "env_snowflake_oauth_token",
    },
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
        "--snowflake-authenticator",
        "externalbrowser",
        "--snowflake-private-key-path",
        str(assets_path / "private_key.txt"),
        "--snowflake-token-path",
        str(assets_path / "oauth_token_path.txt"),
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
        "--oauth-config",
        json.dumps({"oauth_config_variable": "cli_oauth_config_value"}),
    ],
    {  # expected
        "subcommand": "deploy",
        "config_file_path": assets_path / "schemachange-config.yml",
        "config_version": 1,
        "root_folder": assets_path,
        "modules_folder": assets_path,
        "snowflake_account": "snowflake-account-from-cli",
        "snowflake_user": "snowflake-user-from-cli",
        "snowflake_role": get_snowflake_identifier_string(
            "snowflake-role-from-cli", "placeholder"
        ),
        "snowflake_warehouse": get_snowflake_identifier_string(
            "snowflake-warehouse-from-cli", "placeholder"
        ),
        "snowflake_database": get_snowflake_identifier_string(
            "snowflake-database-from-cli", "placeholder"
        ),
        "snowflake_schema": get_snowflake_identifier_string(
            "snowflake-schema-from-cli", "placeholder"
        ),
        "snowflake_authenticator": "snowflake_jwt",
        "snowflake_private_key_path": assets_path / "alt_private_key.txt",
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
        "snowflake_password": "env_snowflake_password",
    },
    None,
    id="deploy: all env_vars and all cli argument names",
)

deploy_snowflake_oauth_env_var = pytest.param(
    "schemachange.cli.deploy",
    {"SNOWFLAKE_TOKEN": "env_snowflake_oauth_token"},
    [
        "schemachange",
        "deploy",
        *required_args,
        "--snowflake-authenticator",
        "oauth",
        "--snowflake-token-path",
        str(assets_path / "oauth_token_path.txt"),
        "--oauth-config",
        json.dumps({"oauth_config_variable": "cli_oauth_config_value"}),
    ],
    {
        **default_deploy_config,
        "snowflake_account": "account",
        "snowflake_user": "user",
        "snowflake_warehouse": "warehouse",
        "snowflake_role": "role",
        "snowflake_authenticator": "oauth",
        "snowflake_oauth_token": "env_snowflake_oauth_token",
    },
    None,
    id="deploy: oauth env var",
)

deploy_snowflake_oauth_file = pytest.param(
    "schemachange.cli.deploy",
    {},
    [
        "schemachange",
        "deploy",
        *required_args,
        "--snowflake-authenticator",
        "oauth",
        "--snowflake-token-path",
        str(assets_path / "oauth_token_path.txt"),
        "--oauth-config",
        json.dumps({"oauth_config_variable": "cli_oauth_config_value"}),
    ],
    {
        **default_deploy_config,
        "snowflake_account": "account",
        "snowflake_user": "user",
        "snowflake_warehouse": "warehouse",
        "snowflake_role": "role",
        "snowflake_authenticator": "oauth",
        "snowflake_oauth_token": "my-oauth-token\n",
    },
    None,
    id="deploy: oauth file",
)

deploy_snowflake_oauth_request = pytest.param(
    "schemachange.cli.deploy",
    {},
    [
        "schemachange",
        "deploy",
        *required_args,
        "--snowflake-authenticator",
        "oauth",
        "--oauth-config",
        json.dumps({"oauth_config_variable": "cli_oauth_config_value"}),
    ],
    {
        **default_deploy_config,
        "snowflake_account": "account",
        "snowflake_user": "user",
        "snowflake_warehouse": "warehouse",
        "snowflake_role": "role",
        "snowflake_authenticator": "oauth",
        "snowflake_oauth_token": "requested_oauth_token",
    },
    None,
    id="deploy: oauth request",
)

render_only_required = pytest.param(
    "schemachange.cli.render",
    {},
    [
        "schemachange",
        "render",
        str(script_path),
    ],
    {**default_base_config},
    script_path,
    id="render: only required",
)

render_all_cli_arg_names = pytest.param(
    "schemachange.cli.render",
    {},
    [
        "schemachange",
        "render",
        "--root-folder",
        ".",
        "--vars",
        '{"var1": "val"}',
        "--verbose",
        str(script_path),
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
    "to_mock, env_vars, cli_args, expected_config, expected_script_path",
    [
        no_command,
        deploy_only_required,
        deploy_all_cli_arg_names,
        deploy_all_cli_arg_flags,
        deploy_all_env_all_cli,
        deploy_snowflake_oauth_env_var,
        deploy_snowflake_oauth_file,
        deploy_snowflake_oauth_request,
        render_only_required,
        render_all_cli_arg_names,
    ],
)
@mock.patch(
    "schemachange.config.DeployConfig.get_oauth_token",
    return_value="requested_oauth_token",
)
@mock.patch("schemachange.session.SnowflakeSession.snowflake.connector.connect")
def test_main_deploy_subcommand_given_arguments_make_sure_arguments_set_on_call(
    _,
    __,
    to_mock: str,
    env_vars: dict[str, str],
    cli_args: list[str],
    expected_config: dict,
    expected_script_path: Path | None,
):
    with mock.patch.dict(os.environ, env_vars, clear=True):
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
                "snowflake_password": "password",
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
@mock.patch("schemachange.session.SnowflakeSession.snowflake.connector.connect")
def test_main_deploy_config_folder(
    _,
    to_mock: str,
    args: list[str],
    expected_config: dict,
    expected_script_path: Path | None,
):
    with mock.patch.dict(os.environ, {"SNOWFLAKE_PASSWORD": "password"}, clear=True):
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
            ],
            {**default_base_config, "modules_folder": "DUMMY"},
            script_path,
        ),
    ],
)
@mock.patch("schemachange.session.SnowflakeSession.snowflake.connector.connect")
def test_main_deploy_modules_folder(
    _,
    to_mock: str,
    args: list[str],
    expected_config: dict,
    expected_script_path: Path | None,
):
    with mock.patch.dict(os.environ, {"SNOWFLAKE_PASSWORD": "password"}, clear=True):
        with tempfile.TemporaryDirectory() as d:
            # noinspection PyTypeChecker
            args[args.index("DUMMY")] = d
            expected_config["modules_folder"] = Path(d)

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
