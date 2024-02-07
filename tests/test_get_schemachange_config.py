import pathlib

import pytest

from schemachange.cli import get_schemachange_config


def test_get_schemachange_config__using_restricted_jinja_environment_settings_set_should_raise_exception(
            tmp_path: pathlib.Path):
  # Test that we do not allow the user to set Jinja environment variables that would
  # conflict with the default settings
  config_contents = """
config-version: 1.1
vars:
  database_name: SCHEMACHANGE_DEMO_JINJA
jinja:
  autoescape: True
  undefined: ""
  extensions: []
  loader: null
"""
  config_file = tmp_path / "schemachange-config.yml"
  config_file.write_text(config_contents)
  with pytest.raises(ValueError) as e:
    config = get_schemachange_config(str(config_file), None, None, None,
                       None, None, None, None,
                     None,None, None, False,
                          False, None,True, None, None)
  assert str(e.value) == "Restricted Jinja environment settings provided: autoescape, extensions, loader, undefined"


def test_get_schemachange_config__using_invalid_jinja_environment_should_raise_exception(tmp_path: pathlib.Path):
  # Test that Jinja environment is valid if set
  config_contents = """
config-version: 1.1
vars:
  database_name: SCHEMACHANGE_DEMO_JINJA
jinja: test
"""
  config_file = tmp_path / "schemachange-config.yml"
  config_file.write_text(config_contents)

  with pytest.raises(ValueError) as e:
    config = get_schemachange_config(str(config_file), None, None, None,
                        None, None, None, None,
                     None,None, None, False,
                          False, False,True, None, None)
  assert str(e.value) == "jinja did not parse correctly, please check its configuration"
