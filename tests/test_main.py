import os
import sys
import pytest
import unittest.mock as mock
import schemachange.cli 
import tempfile
from textwrap import dedent

DEFAULT_CONFIG = {
    'root-folder': os.path.abspath('.'),
    'modules-folder': None,
    'snowflake-account': None,
    'snowflake-user': None,
    'snowflake-role':None,
    'snowflake-warehouse': None,
    'snowflake-database': None,
    'change-history-table': None,
    'vars': {},
    'create-change-history-table': False,
    'autocommit': False,
    'verbose': False,
    'dry-run': False,
}

@pytest.mark.parametrize("args, expected", [
    (["schemachange"], DEFAULT_CONFIG),
    (["schemachange", "deploy"], DEFAULT_CONFIG),
    (["schemachange", "deploy", "-f", '.'],
        {**DEFAULT_CONFIG, 'root-folder':os.path.abspath('.')}),
    (["schemachange", "deploy", "--snowflake-account", "account"],
        {**DEFAULT_CONFIG, 'snowflake-account': 'account'}),
    (["schemachange", "deploy", "--snowflake-user", "user"],
        {**DEFAULT_CONFIG, 'snowflake-user': 'user'}),
    (["schemachange", "deploy", "--snowflake-role", "role"],
        {**DEFAULT_CONFIG, 'snowflake-role': 'role'}),
    (["schemachange", "deploy", "--snowflake-warehouse", "warehouse"],
        {**DEFAULT_CONFIG, 'snowflake-warehouse': 'warehouse'}),
    (["schemachange", "deploy", "--snowflake-database", "database"],
        {**DEFAULT_CONFIG, 'snowflake-database': 'database'}),
    (["schemachange", "deploy", "--change-history-table", "db.schema.table"],
        {**DEFAULT_CONFIG, 'change-history-table': 'db.schema.table'}),
    (["schemachange", "deploy", "--vars", '{"var1": "val"}'],
        {**DEFAULT_CONFIG, 'vars': {'var1' : 'val'},}),
    (["schemachange", "deploy", "--create-change-history-table"],
        {**DEFAULT_CONFIG, 'create-change-history-table': True}),
    (["schemachange", "deploy", "--autocommit"],
        {**DEFAULT_CONFIG, 'autocommit': True}),
    (["schemachange", "deploy", "--verbose"],
        {**DEFAULT_CONFIG, 'verbose': True}),
    (["schemachange", "deploy", "--dry-run"],
        {**DEFAULT_CONFIG, 'dry-run': True}),
])

def test_main_deploy_subcommand_given_arguments_make_sure_arguments_set_on_call( args, expected):
    sys.argv = args
    
    with mock.patch("schemachange.cli.deploy_command") as mock_deploy_command:
        schemachange.cli.main()
        mock_deploy_command.assert_called_once()
        [config,], _call_kwargs = mock_deploy_command.call_args
        assert config == expected

@pytest.mark.parametrize("args, to_mock, expected_args", [
    (["schemachange", "deploy", "--config-folder", "DUMMY"],
        "schemachange.cli.deploy_command",
        ({**DEFAULT_CONFIG, 'snowflake-account': 'account'},)),
    (["schemachange", "render", "script.sql", "--config-folder", "DUMMY"],
        "schemachange.cli.render_command",
        ({**DEFAULT_CONFIG, 'snowflake-account': 'account'}, "script.sql"))
])
def test_main_deploy_config_folder(args, to_mock, expected_args):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, 'schemachange-config.yml'), 'wt') as f:
            f.write(dedent('''
                snowflake-account: account
            '''))

        args[args.index("DUMMY")] = d
        sys.argv = args

        with mock.patch(to_mock) as mock_command:
            schemachange.cli.main()
            mock_command.assert_called_once()
            call_args, _call_kwargs = mock_command.call_args
            assert call_args == expected_args


@pytest.mark.parametrize("args, to_mock, expected_args", [
    (["schemachange", "deploy", "--modules-folder", "DUMMY"],
        "schemachange.cli.deploy_command",
        ({**DEFAULT_CONFIG, 'modules-folder': 'DUMMY'},)),
    (["schemachange", "render", "script.sql", "--modules-folder", "DUMMY"],
        "schemachange.cli.render_command",
        ({**DEFAULT_CONFIG, 'modules-folder': 'DUMMY'}, "script.sql"))
])
def test_main_deploy_modules_folder(args, to_mock, expected_args):
    with tempfile.TemporaryDirectory() as d:

        args[args.index("DUMMY")] = d
        expected_args[0]['modules-folder'] = d
        sys.argv = args

        with mock.patch(to_mock) as mock_command:
            schemachange.cli.main()
            mock_command.assert_called_once()
            call_args, _call_kwargs = mock_command.call_args
            assert call_args == expected_args

@pytest.mark.parametrize("args, expected", [
    (["schemachange", "render", "script.sql"],
        ({**DEFAULT_CONFIG}, "script.sql")),
    # (["schemachange", "render", "--config-folder", "test", "script.sql"],
    #     ("test", None, None, None, False, "script.sql")),
    (["schemachange", "render", "--root-folder", '.', "script.sql"],
        ({**DEFAULT_CONFIG, 'root-folder': os.path.abspath('.')}, "script.sql")),
    #(["schemachange", "render", "--modules-folder", "modules-folder", "script.sql"], ('.', None, "modules-folder", None, False, "script.sql")),
    (["schemachange", "render", "--vars", '{"var1": "val"}', "script.sql"],
        ({**DEFAULT_CONFIG, 'vars': {"var1": "val"}}, "script.sql")),
    (["schemachange", "render", "--verbose", "script.sql"],
        ({**DEFAULT_CONFIG, 'verbose': True}, "script.sql")),
])
def test_main_render_subcommand_given_arguments_make_sure_arguments_set_on_call( args, expected):
    sys.argv = args
    
    with mock.patch("schemachange.cli.render_command") as mock_render_command:
        schemachange.cli.main()
        mock_render_command.assert_called_once()
        call_args, _call_kwargs = mock_render_command.call_args
        assert call_args == expected
