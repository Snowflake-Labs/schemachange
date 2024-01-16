import os
import tempfile
import unittest.mock as mock
from pathlib import Path
from textwrap import dedent

import pytest

import schemachange.cli as cli

default_deploy_config = {
    # Shared configuration options
    "config_folder": Path("."),
    "root_folder": Path("."),
    "modules_folder": None,
    "vars": {},
    "verbose": False,
    # Deploy configuration options
    "snowflake_account": None,
    "snowflake_user": None,
    "snowflake_role": None,
    "snowflake_warehouse": None,
    "snowflake_database": None,
    "snowflake_schema": None,
    "change_history_table": "METADATA.SCHEMACHANGE.CHANGE_HISTORY",
    "create_change_history_table": False,
    "autocommit": False,
    "dry_run": False,
    "query_tag": None,
    "oauth_config": None,
    "version_number_validation_regex": None,
    "raise_exception_on_ignored_versioned_migration": False,
}


@pytest.mark.parametrize(
    "cli_args, expected",
    [
        (["schemachange"], default_deploy_config),
        (["schemachange", "deploy"], default_deploy_config),
        (
            ["schemachange", "deploy", "-f", "."],
            {**default_deploy_config, "root_folder": Path(".")},
        ),
        (
            ["schemachange", "deploy", "--snowflake-account", "account"],
            {**default_deploy_config, "snowflake_account": "account"},
        ),
        (
            ["schemachange", "deploy", "--snowflake-user", "user"],
            {**default_deploy_config, "snowflake_user": "user"},
        ),
        (
            ["schemachange", "deploy", "--snowflake-role", "role"],
            {**default_deploy_config, "snowflake_role": "role"},
        ),
        (
            ["schemachange", "deploy", "--snowflake-warehouse", "warehouse"],
            {**default_deploy_config, "snowflake_warehouse": "warehouse"},
        ),
        (
            ["schemachange", "deploy", "--snowflake-database", "database"],
            {**default_deploy_config, "snowflake_database": "database"},
        ),
        (
            ["schemachange", "deploy", "--snowflake-schema", "schema"],
            {**default_deploy_config, "snowflake_schema": "schema"},
        ),
        (
            ["schemachange", "deploy", "--change-history-table", "db.schema.table"],
            {**default_deploy_config, "change_history_table": "db.schema.table"},
        ),
        (
            ["schemachange", "deploy", "--vars", '{"var1": "val"}'],
            {
                **default_deploy_config,
                "vars": {"var1": "val"},
            },
        ),
        (
            ["schemachange", "deploy", "--create-change-history-table"],
            {**default_deploy_config, "create_change_history_table": True},
        ),
        (
            ["schemachange", "deploy", "--autocommit"],
            {**default_deploy_config, "autocommit": True},
        ),
        (
            ["schemachange", "deploy", "--verbose"],
            {**default_deploy_config, "verbose": True},
        ),
        (
            ["schemachange", "deploy", "--dry-run"],
            {**default_deploy_config, "dry_run": True},
        ),
        (
            ["schemachange", "deploy", "--query-tag", "querytag"],
            {**default_deploy_config, "query_tag": "querytag"},
        ),
        (
            [
                "schemachange",
                "deploy",
                "--oauth-config",
                '{"token-provider-url": "https//..."}',
            ],
            {
                **default_deploy_config,
                "oauth_config": {"token-provider-url": "https//..."},
            },
        ),
    ],
)
@mock.patch("schemachange.cli.deploy_command")
def test_main_deploy_subcommand_given_arguments_make_sure_arguments_set_on_call(
    mock_deploy_command, cli_args, expected
):
    with mock.patch("sys.argv", cli_args):
        cli.main()
        mock_deploy_command.assert_called_once()
        _, call_kwargs = mock_deploy_command.call_args
        for expected_arg, expected_value in expected.items():
            actual_value = getattr(call_kwargs["config"], expected_arg)
            assert actual_value == expected_value


@pytest.mark.parametrize(
    "cli_args, expected",
    [
        (
            [
                "schemachange",
                "render",
                str(Path(__file__).parent / "assets" / "script.sql"),
            ],
            (
                {**default_deploy_config},
                Path(__file__).parent / "assets" / "script.sql",
            ),
        ),
        (
            [
                "schemachange",
                "render",
                "--root-folder",
                ".",
                str(Path(__file__).parent / "assets" / "script.sql"),
            ],
            (
                {**default_deploy_config, "root_folder": Path(".")},
                Path(__file__).parent / "assets" / "script.sql",
            ),
        ),
        (
            [
                "schemachange",
                "render",
                "--vars",
                '{"var1": "val"}',
                str(Path(__file__).parent / "assets" / "script.sql"),
            ],
            (
                {**default_deploy_config, "vars": {"var1": "val"}},
                Path(__file__).parent / "assets" / "script.sql",
            ),
        ),
        (
            [
                "schemachange",
                "render",
                "--verbose",
                str(Path(__file__).parent / "assets" / "script.sql"),
            ],
            (
                {**default_deploy_config, "verbose": True},
                Path(__file__).parent / "assets" / "script.sql",
            ),
        ),
    ],
)
@mock.patch("schemachange.cli.render")
def test_main_render_subcommand_given_arguments_make_sure_arguments_set_on_call(
    mock_render_command, cli_args, expected
):
    expected_config, expected_script = expected

    with mock.patch("sys.argv", cli_args):
        cli.main()
        mock_render_command.assert_called_once()
        _, call_kwargs = mock_render_command.call_args
        for expected_arg, expected_value in expected_config.items():
            actual_value = getattr(call_kwargs["config"], expected_arg)
            assert actual_value == expected_value
        assert call_kwargs["script_path"] == expected_script


@pytest.mark.parametrize(
    "args, to_mock, expected_args",
    [
        (
            ["schemachange", "deploy", "--config-folder", "DUMMY"],
            "schemachange.cli.deploy_command",
            ({**default_deploy_config, "snowflake_account": "account"},),
        ),
        (
            [
                "schemachange",
                "render",
                str(Path(__file__).parent / "assets" / "script.sql"),
                "--config-folder",
                "DUMMY",
            ],
            "schemachange.cli.render",
            (
                {**default_deploy_config, "snowflake_account": "account"},
                Path(__file__).parent / "assets" / "script.sql",
            ),
        ),
    ],
)
def test_main_deploy_config_folder(args, to_mock, expected_args):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "schemachange-config.yml"), "wt") as f:
            f.write(
                dedent(
                    """
                snowflake_account: account
            """
                )
            )

        args[args.index("DUMMY")] = d
        expected_args[0]["config_folder"] = Path(d)

        with mock.patch(to_mock) as mock_command:
            with mock.patch("sys.argv", args):
                cli.main()
                mock_command.assert_called_once()
                _, call_kwargs = mock_command.call_args
                for expected_arg, expected_value in expected_args[0].items():
                    actual_value = getattr(call_kwargs["config"], expected_arg)
                    assert actual_value == expected_value
                if len(expected_args) == 2:
                    assert call_kwargs["script_path"] == expected_args[1]


@pytest.mark.parametrize(
    "args, to_mock, expected_args",
    [
        (
            ["schemachange", "deploy", "--modules-folder", "DUMMY"],
            "schemachange.cli.deploy_command",
            ({**default_deploy_config, "modules_folder": "DUMMY"},),
        ),
        (
            [
                "schemachange",
                "render",
                str(Path(__file__).parent / "assets" / "script.sql"),
                "--modules-folder",
                "DUMMY",
            ],
            "schemachange.cli.render",
            (
                {**default_deploy_config, "modules_folder": "DUMMY"},
                Path(__file__).parent / "assets" / "script.sql",
            ),
        ),
    ],
)
def test_main_deploy_modules_folder(args, to_mock, expected_args):
    with tempfile.TemporaryDirectory() as d:
        args[args.index("DUMMY")] = d
        expected_args[0]["modules_folder"] = Path(d)

        with mock.patch(to_mock) as mock_command:
            with mock.patch("sys.argv", args):
                cli.main()
                mock_command.assert_called_once()
                _, call_kwargs = mock_command.call_args
                for expected_arg, expected_value in expected_args[0].items():
                    actual_value = getattr(call_kwargs["config"], expected_arg)
                    assert actual_value == expected_value
                if len(expected_args) == 2:
                    assert call_kwargs["script_path"] == expected_args[1]
