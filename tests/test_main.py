import os
import sys
import pytest
import unittest.mock as mock
import schemachange.cli 


@pytest.mark.parametrize("args, expected", [
    (["schemachange"], ('.', None, None, None, None, None, None, None, None, None, False, False, False, False)),
    (["schemachange", "--config-folder", "test"], ('test', None, None, None, None, None, None, None, None, None, False, False, False, False)),
    (["schemachange", "-f", '.'], ('.', '.', None, None, None, None, None, None, None, None, False, False, False, False)),     
    (["schemachange", "--modules-folder", "modules-folder"], ('.', None, "modules-folder", None, None, None, None, None, None, None, False, False, False, False)),
    (["schemachange", "--snowflake-account", "account"], ('.', None, None, "account", None, None, None, None, None, None, False, False, False, False)),
    (["schemachange", "--snowflake-user", "user"], ('.', None, None, None, "user", None, None, None, None, None, False, False, False, False)),
    (["schemachange", "--snowflake-role", "role"], ('.', None, None, None, None, "role", None, None, None, None, False, False, False, False)),
    (["schemachange", "--snowflake-warehouse", "warehouse"], ('.', None, None, None, None, None, "warehouse", None, None, None, False, False, False, False)),
    (["schemachange", "--snowflake-database", "database"], ('.', None, None, None, None, None, None, "database", None, None, False, False, False, False)),    
    (["schemachange", "--change-history-table", "db.schema.table"], ('.', None, None, None, None, None, None, None, "db.schema.table", None, False, False, False, False)),    
    (["schemachange", "--vars", '{"var1": "val"}'], ('.', None, None, None, None, None, None, None, None, {'var1' : 'val'}, False, False, False, False)),
    (["schemachange", "--create-change-history-table"], ('.', None, None, None, None, None, None, None, None, None, True, False, False, False)),
    (["schemachange", "--autocommit"], ('.', None, None, None, None, None, None, None, None, None, False, True, False, False)),
    (["schemachange", "--verbose"], ('.', None, None, None, None, None, None, None, None, None, False, False, True, False)),
    (["schemachange", "--dry-run"], ('.', None, None, None, None, None, None, None, None, None, False, False, False, True))       
])
def test_main_no_subcommand_given_arguments_make_sure_arguments_set_on_call( args, expected):
    sys.argv = args
    
    with mock.patch("schemachange.cli.schemachange") as mock_schemachange:
        schemachange.cli.main()
        mock_schemachange.assert_called_once_with(*expected)


@pytest.mark.parametrize("args, expected", [
    (["schemachange", "deploy"], ('.', None, None, None, None, None, None, None, None, None, False, False, False, False)),
    (["schemachange", "deploy", "--config-folder", "test"], ('test', None, None, None, None, None, None, None, None, None, False, False, False, False)),
    (["schemachange", "deploy", "-f", '.'], ('.', '.', None, None, None, None, None, None, None, None, False, False, False, False)),     
    (["schemachange", "deploy", "--modules-folder", "modules-folder"], ('.', None, "modules-folder", None, None, None, None, None, None, None, False, False, False, False)),
    (["schemachange", "deploy", "--snowflake-account", "account"], ('.', None, None, "account", None, None, None, None, None, None, False, False, False, False)),
    (["schemachange", "deploy", "--snowflake-user", "user"], ('.', None, None, None, "user", None, None, None, None, None, False, False, False, False)),
    (["schemachange", "deploy", "--snowflake-role", "role"], ('.', None, None, None, None, "role", None, None, None, None, False, False, False, False)),
    (["schemachange", "deploy", "--snowflake-warehouse", "warehouse"], ('.', None, None, None, None, None, "warehouse", None, None, None, False, False, False, False)),
    (["schemachange", "deploy", "--snowflake-database", "database"], ('.', None, None, None, None, None, None, "database", None, None, False, False, False, False)),    
    (["schemachange", "deploy", "--change-history-table", "db.schema.table"], ('.', None, None, None, None, None, None, None, "db.schema.table", None, False, False, False, False)),    
    (["schemachange", "deploy", "--vars", '{"var1": "val"}'], ('.', None, None, None, None, None, None, None, None, {'var1' : 'val'}, False, False, False, False)),
    (["schemachange", "deploy", "--create-change-history-table"], ('.', None, None, None, None, None, None, None, None, None, True, False, False, False)),
    (["schemachange", "deploy", "--autocommit"], ('.', None, None, None, None, None, None, None, None, None, False, True, False, False)),
    (["schemachange", "deploy", "--verbose"], ('.', None, None, None, None, None, None, None, None, None, False, False, True, False)),
    (["schemachange", "deploy", "--dry-run"], ('.', None, None, None, None, None, None, None, None, None, False, False, False, True))
       
])
def test_main_deploy_subcommand_given_arguments_make_sure_arguments_set_on_call( args, expected):
    sys.argv = args
    
    with mock.patch("schemachange.cli.schemachange") as mock_schemachange:
        schemachange.cli.main()
        mock_schemachange.assert_called_once_with(*expected)


@pytest.mark.parametrize("args, expected", [
    (["schemachange", "render", "script.sql"], ('.', None, None, None, False, "script.sql")),
    (["schemachange", "render", "--config-folder", "test", "script.sql"], ("test", None, None, None, False, "script.sql")),
    (["schemachange", "render", "--root-folder", '.', "script.sql"], ('.', ".", None, None, False, "script.sql")),
    (["schemachange", "render", "--modules-folder", "modules-folder", "script.sql"], ('.', None, "modules-folder", None, False, "script.sql")),
    (["schemachange", "render", "--vars", '{"var1": "val"}', "script.sql"], ('.', None, None, {'var1' : 'val'}, False, "script.sql")),
    (["schemachange", "render", "--verbose", "script.sql"], ('.', None, None, None, True, "script.sql")),      
])
def test_main_render_subcommand_given_arguments_make_sure_arguments_set_on_call( args, expected):
    sys.argv = args
    
    with mock.patch("schemachange.cli.render_command") as mock_render_command:
        schemachange.cli.main()
        mock_render_command.assert_called_once_with(*expected)
