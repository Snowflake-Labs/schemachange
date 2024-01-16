import os
import unittest.mock as mock
from pathlib import Path

import pytest

from schemachange.get_yaml_config import load_yaml_config, get_yaml_config


# Note Paramters in config file are kebab case  and are re-rendered as snake case after
# 'load_yaml_config' is called


def test__load_yaml_config__simple_config_file(tmp_path: Path):
    config_contents = """
config-version: 1
root-folder: scripts
modules-folder: modules
vars:
  database_name: SCHEMACHANGE_DEMO_JINJA
"""
    config_file = tmp_path / "schemachange-config.yml"
    config_file.write_text(config_contents)

    config = load_yaml_config(config_file)

    assert config["config-version"] == 1
    assert config["root-folder"] == "scripts"
    assert config["modules-folder"] == "modules"
    assert config["vars"]["database_name"] == "SCHEMACHANGE_DEMO_JINJA"


@mock.patch.dict(os.environ, {"TEST_VAR": "env_value"})
def test__load_yaml_config__with_env_var_should_populate_value(
    tmp_path: Path,
):
    config_contents = """
config-version: 1.1
root-folder: {{env_var('TEST_VAR')}}
modules-folder: modules
vars:
  database_name: SCHEMACHANGE_DEMO_JINJA
"""
    config_file = tmp_path / "schemachange-config.yml"
    config_file.write_text(config_contents)

    config = load_yaml_config(config_file)

    assert config["root-folder"] == "env_value"


def test__load_yaml_config__requiring_env_var_but_env_var_not_set_should_raise_exception(
    tmp_path: Path,
):
    config_contents = """
config-version: 1.1
root-folder: {{env_var('TEST_VAR')}}
modules-folder: modules
vars:
  database_name: SCHEMACHANGE_DEMO_JINJA
"""
    config_file = tmp_path / "schemachange-config.yml"
    config_file.write_text(config_contents)

    with pytest.raises(ValueError) as e:
        load_yaml_config(config_file)
    assert (
        str(e.value)
        == "Could not find environmental variable TEST_VAR and no default value was provided"
    )


@mock.patch("pathlib.Path.is_dir", return_value=True)
def test__get_yaml_config(_):
    config_file_path = (
        Path(__file__).parent / "assets" / "schemachange-config-complete.yml"
    )
    yaml_config = get_yaml_config(
        subcommand="deploy", config_file_path=config_file_path
    )
    assert yaml_config.root_folder == Path("root-folder-from-yaml")
    assert yaml_config.modules_folder == Path("modules-folder-from-yaml")
    assert yaml_config.snowflake_account == "snowflake-account-from-yaml"
    assert yaml_config.snowflake_user == "snowflake-user-from-yaml"
    assert yaml_config.snowflake_role == "snowflake-role-from-yaml"
    assert yaml_config.snowflake_warehouse == "snowflake-warehouse-from-yaml"
    assert yaml_config.snowflake_database == "snowflake-database-from-yaml"
    assert yaml_config.snowflake_schema == "snowflake-schema-from-yaml"
    assert yaml_config.change_history_table == "change-history-table-from-yaml"
    assert yaml_config.query_tag == "query-tag-from-yaml"

    assert yaml_config.create_change_history_table is False
    assert yaml_config.autocommit is False
    assert yaml_config.dry_run is False

    assert yaml_config.vars == {"var1": "from_yaml"}
    assert yaml_config.oauth_config == {
        "token-provider-url": "token-provider-url-from-yaml",
        "token-request-headers": {
            "Content-Type": "Content-Type-from-yaml",
            "User-Agent": "User-Agent-from-yaml",
        },
        "token-request-payload": {
            "client_id": "id-from-yaml",
            "grant_type": "type-from-yaml",
            "password": "password-from-yaml",
            "scope": "scope-from-yaml",
            "username": "username-from-yaml",
        },
        "token-response-name": "token-response-name-from-yaml",
    }
