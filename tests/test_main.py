import os
import tempfile
import unittest.mock as mock
from textwrap import dedent

import pytest

import schemachange.cli as cli


@pytest.mark.parametrize(
    "args, expected",
    [
        (["schemachange"], cli.CONFIG_DEFAULTS),
        (["schemachange", "deploy"], cli.CONFIG_DEFAULTS),
        (
            ["schemachange", "deploy", "-f", "."],
            {**cli.CONFIG_DEFAULTS, "root_folder": os.path.abspath(".")},
        ),
        (
            ["schemachange", "deploy", "--snowflake-account", "account"],
            {**cli.CONFIG_DEFAULTS, "snowflake_account": "account"},
        ),
        (
            ["schemachange", "deploy", "--snowflake-user", "user"],
            {**cli.CONFIG_DEFAULTS, "snowflake_user": "user"},
        ),
        (
            ["schemachange", "deploy", "--snowflake-role", "role"],
            {**cli.CONFIG_DEFAULTS, "snowflake_role": "role"},
        ),
        (
            ["schemachange", "deploy", "--snowflake-warehouse", "warehouse"],
            {**cli.CONFIG_DEFAULTS, "snowflake_warehouse": "warehouse"},
        ),
        (
            ["schemachange", "deploy", "--snowflake-database", "database"],
            {**cli.CONFIG_DEFAULTS, "snowflake_database": "database"},
        ),
        (
            ["schemachange", "deploy", "--snowflake-schema", "schema"],
            {**cli.CONFIG_DEFAULTS, "snowflake_schema": "schema"},
        ),
        (
            ["schemachange", "deploy", "--change-history-table", "db.schema.table"],
            {**cli.CONFIG_DEFAULTS, "change_history_table": "db.schema.table"},
        ),
        (
            ["schemachange", "deploy", "--vars", '{"var1": "val"}'],
            {
                **cli.CONFIG_DEFAULTS,
                "vars": {"var1": "val"},
            },
        ),
        (
            ["schemachange", "deploy", "--create-change-history-table"],
            {**cli.CONFIG_DEFAULTS, "create_change_history_table": True},
        ),
        (
            ["schemachange", "deploy", "--autocommit"],
            {**cli.CONFIG_DEFAULTS, "autocommit": True},
        ),
        (
            ["schemachange", "deploy", "--verbose"],
            {**cli.CONFIG_DEFAULTS, "verbose": True},
        ),
        (
            ["schemachange", "deploy", "--dry-run"],
            {**cli.CONFIG_DEFAULTS, "dry_run": True},
        ),
        (
            ["schemachange", "deploy", "--query-tag", "querytag"],
            {**cli.CONFIG_DEFAULTS, "query_tag": "querytag"},
        ),
        (
            [
                "schemachange",
                "deploy",
                "--oauth-config",
                '{"token-provider-url": "https//..."}',
            ],
            {
                **cli.CONFIG_DEFAULTS,
                "oauth_config": {"token-provider-url": "https//..."},
            },
        ),
    ],
)
def test_main_deploy_subcommand_given_arguments_make_sure_arguments_set_on_call(
    args, expected
):
    with mock.patch("schemachange.cli.deploy_command") as mock_deploy_command:
        cli.main(args)
        mock_deploy_command.assert_called_once()
        [
            config,
        ], _call_kwargs = mock_deploy_command.call_args
        assert config == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        (
            ["schemachange", "render", "script.sql"],
            ({**cli.CONFIG_DEFAULTS}, "script.sql"),
        ),
        (
            ["schemachange", "render", "--root-folder", ".", "script.sql"],
            (
                {**cli.CONFIG_DEFAULTS, "root_folder": os.path.abspath(".")},
                "script.sql",
            ),
        ),
        (
            ["schemachange", "render", "--vars", '{"var1": "val"}', "script.sql"],
            ({**cli.CONFIG_DEFAULTS, "vars": {"var1": "val"}}, "script.sql"),
        ),
        (
            ["schemachange", "render", "--verbose", "script.sql"],
            ({**cli.CONFIG_DEFAULTS, "verbose": True}, "script.sql"),
        ),
    ],
)
def test_main_render_subcommand_given_arguments_make_sure_arguments_set_on_call(
    args, expected
):
    with mock.patch("schemachange.cli.render_command") as mock_render_command:
        cli.main(args)
        mock_render_command.assert_called_once()
        call_args, _call_kwargs = mock_render_command.call_args
        assert call_args == expected


@pytest.mark.parametrize(
    "args, to_mock, expected_args",
    [
        (
            ["schemachange", "deploy", "--config-folder", "DUMMY"],
            "schemachange.cli.deploy_command",
            ({**cli.CONFIG_DEFAULTS, "snowflake_account": "account"},),
        ),
        (
            ["schemachange", "render", "script.sql", "--config-folder", "DUMMY"],
            "schemachange.cli.render_command",
            ({**cli.CONFIG_DEFAULTS, "snowflake_account": "account"}, "script.sql"),
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

        with mock.patch(to_mock) as mock_command:
            cli.main(args)
            mock_command.assert_called_once()
            call_args, _call_kwargs = mock_command.call_args
            assert call_args == expected_args


@pytest.mark.parametrize(
    "args, to_mock, expected_args",
    [
        (
            ["schemachange", "deploy", "--modules-folder", "DUMMY"],
            "schemachange.cli.deploy_command",
            ({**cli.CONFIG_DEFAULTS, "modules_folder": "DUMMY"},),
        ),
        (
            ["schemachange", "render", "script.sql", "--modules-folder", "DUMMY"],
            "schemachange.cli.render_command",
            ({**cli.CONFIG_DEFAULTS, "modules_folder": "DUMMY"}, "script.sql"),
        ),
    ],
)
def test_main_deploy_modules_folder(args, to_mock, expected_args):
    with tempfile.TemporaryDirectory() as d:
        args[args.index("DUMMY")] = d
        expected_args[0]["modules_folder"] = d

        with mock.patch(to_mock) as mock_command:
            cli.main(args)
            mock_command.assert_called_once()
            call_args, _call_kwargs = mock_command.call_args
            assert call_args == expected_args
