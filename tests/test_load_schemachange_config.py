import os
import pathlib
import unittest.mock as mock

import pytest

from schemachange.cli import load_schemachange_config

# Note Paramters in config file are kebab case  and are re-rendered as snake case after 'load_schemachange_config' is called


def test__load_schemachange_config__simple_config_file(tmp_path: pathlib.Path):

    config_contents = """
config-version: 1
root-folder: scripts
modules-folder: modules
vars:
  database_name: SCHEMACHANGE_DEMO_JINJA
"""
    config_file = tmp_path / "schemachange-config.yml"
    config_file.write_text(config_contents)

    config = load_schemachange_config(str(config_file))

    assert config["config-version"] == 1
    assert config["root-folder"] == "scripts"
    assert config["modules-folder"] == "modules"
    assert config["vars"]["database_name"] == "SCHEMACHANGE_DEMO_JINJA"


@mock.patch.dict(os.environ, {"TEST_VAR": "env_value"})
def test__load_schemachange_config__with_env_var_should_populate_value(
    tmp_path: pathlib.Path,
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

    config = load_schemachange_config(str(config_file))

    assert config["root-folder"] == "env_value"


def test__load_schemachange_config__requiring_env_var_but_env_var_not_set_should_raise_exception(
    tmp_path: pathlib.Path,
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
        config = load_schemachange_config(str(config_file))
    assert (
        str(e.value)
        == "Could not find environmental variable TEST_VAR and no default value was provided"
    )
