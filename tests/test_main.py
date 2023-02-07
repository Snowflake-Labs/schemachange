import os
import tempfile
import unittest.mock as mock
from textwrap import dedent

import pytest

import schemachange.cli

DEFAULT_CONFIG = {
    'root_folder': os.path.abspath('.'),
    'config_file_path':os.path.abspath('.'),
    'modules_folder': None,
    'snowflake_account': None,
    'snowflake_user': None,
    'snowflake_role':None,
    'snowflake_warehouse': None,
    'snowflake_database': None,
    'change_history_table': None,
    'vars': {},
    'create_change_history_table': False,
    'autocommit': False,
    'verbose': False,
    'dry_run': False,
    'query_tag': None,
    'oauth_config':{},
}


@pytest.mark.parametrize("args, expected", [
    (["schemachange"], DEFAULT_CONFIG),
    (["schemachange", "deploy"], DEFAULT_CONFIG),
    (["schemachange", "deploy", "-f", '.'],
        {**DEFAULT_CONFIG, 'root_folder':os.path.abspath('.')}),
    (["schemachange", "deploy", "--snowflake-account", "account"],
        {**DEFAULT_CONFIG, 'snowflake_account': 'account'}),
    (["schemachange", "deploy", "--snowflake-user", "user"],
        {**DEFAULT_CONFIG, 'snowflake_user': 'user'}),
    (["schemachange", "deploy", "--snowflake-role", "role"],
        {**DEFAULT_CONFIG, 'snowflake_role': 'role'}),
    (["schemachange", "deploy", "--snowflake-warehouse", "warehouse"],
        {**DEFAULT_CONFIG, 'snowflake_warehouse': 'warehouse'}),
    (["schemachange", "deploy", "--snowflake-database", "database"],
        {**DEFAULT_CONFIG, 'snowflake_database': 'database'}),
    (["schemachange", "deploy", "--change-history-table", "db.schema.table"],
        {**DEFAULT_CONFIG, 'change_history_table': 'db.schema.table'}),
    (["schemachange", "deploy", "--vars", '{"var1": "val"}'],
        {**DEFAULT_CONFIG, 'vars': {'var1' : 'val'},}),
    (["schemachange", "deploy", "--create-change-history-table"],
        {**DEFAULT_CONFIG, 'create_change_history_table': True}),
    (["schemachange", "deploy", "--autocommit"],
        {**DEFAULT_CONFIG, 'autocommit': True}),
    (["schemachange", "deploy", "--verbose"],
        {**DEFAULT_CONFIG, 'verbose': True}),
    (["schemachange", "deploy", "--dry-run"],
        {**DEFAULT_CONFIG, 'dry_run': True}),
    (["schemachange", "deploy", "--query-tag", "querytag"],
        {**DEFAULT_CONFIG, 'query_tag': 'querytag'}),
    (["schemachange", "deploy", "--oauth-config", '{"token-provider-url": "https//..."}'],
        {**DEFAULT_CONFIG, 'oauth_config': {"token-provider-url": "https//..."},}),
])
def test_main_deploy_subcommand_given_arguments_make_sure_arguments_set_on_call( args, expected):

    with mock.patch("schemachange.cli.deploy_command") as mock_deploy_command:
        schemachange.cli.main(args)
        mock_deploy_command.assert_called_once()
        [config,], _call_kwargs = mock_deploy_command.call_args
        assert config == expected


@pytest.mark.parametrize("args, expected", [
    (["schemachange", "render", "script.sql"],
        ({**DEFAULT_CONFIG}, "script.sql")),
    (["schemachange", "render", "--root-folder", '.', "script.sql"],
        ({**DEFAULT_CONFIG, 'root_folder': os.path.abspath('.')}, "script.sql")),
    (["schemachange", "render", "--vars", '{"var1": "val"}', "script.sql"],
        ({**DEFAULT_CONFIG, 'vars': {"var1": "val"}}, "script.sql")),
    (["schemachange", "render", "--verbose", "script.sql"],
        ({**DEFAULT_CONFIG, 'verbose': True}, "script.sql")),
])
def test_main_render_subcommand_given_arguments_make_sure_arguments_set_on_call( args, expected):

    with mock.patch("schemachange.cli.render_command") as mock_render_command:
        schemachange.cli.main(args)
        mock_render_command.assert_called_once()
        call_args, _call_kwargs = mock_render_command.call_args
        assert call_args == expected


@pytest.mark.parametrize("args, to_mock, expected_args", [
    (["schemachange", "deploy", "--config-folder", "DUMMY"],
        "schemachange.cli.deploy_command",
        ({**DEFAULT_CONFIG, 'snowflake-account': 'account'},)),
    (["schemachange", "render", "script.sql", "--config-folder", "DUMMY"],
        "schemachange.cli.render_command",
        ({**DEFAULT_CONFIG, 'snowflake_account': 'account'}, "script.sql"))
])
def test_main_deploy_config_folder(args, to_mock, expected_args):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, 'schemachange-config.yml'), 'wt') as f:
            f.write(dedent('''
                snowflake_account: account
            '''))

        args[args.index("DUMMY")] = d

        with mock.patch(to_mock) as mock_command:
            schemachange.cli.main(args)
            mock_command.assert_called_once()
            call_args, _call_kwargs = mock_command.call_args
            assert call_args == expected_args


@pytest.mark.parametrize("args, to_mock, expected_args", [
    (["schemachange", "deploy", "--modules-folder", "DUMMY"],
        "schemachange.cli.deploy_command",
        ({**DEFAULT_CONFIG, 'modules_folder': 'DUMMY'},)),
    (["schemachange", "render", "script.sql", "--modules-folder", "DUMMY"],
        "schemachange.cli.render_command",
        ({**DEFAULT_CONFIG, 'modules_folder': 'DUMMY'}, "script.sql"))
])
def test_main_deploy_modules_folder(args, to_mock, expected_args):
    with tempfile.TemporaryDirectory() as d:

        args[args.index("DUMMY")] = d
        expected_args[0]['modules_folder'] = d

        with mock.patch(to_mock) as mock_command:
            schemachange.cli.main(args)
            mock_command.assert_called_once()
            call_args, _call_kwargs = mock_command.call_args
            assert call_args == expected_args
