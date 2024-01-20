import os
import unittest.mock as mock
import jinja2
import pytest

from schemachange.JinjaEnvVar import JinjaEnvVar


@mock.patch.dict(os.environ, {}, clear=True)
def test_env_var_with_no_default_and_no_environmental_variables_should_raise_exception():
    assert ("SF_DATABASE" in os.environ) is False

    with pytest.raises(ValueError) as e:
        JinjaEnvVar.env_var("SF_DATABASE")
    assert (
        str(e.value)
        == "Could not find environmental variable SF_DATABASE and no default value was provided"
    )


@mock.patch.dict(os.environ, {}, clear=True)
def test_env_var_with_default_and_no_environmental_variables_should_return_default():
    assert ("SF_DATABASE" in os.environ) is False

    result = JinjaEnvVar.env_var("SF_DATABASE", "SCHEMACHANGE_DEMO")
    assert result == "SCHEMACHANGE_DEMO"


@mock.patch.dict(os.environ, {"SF_DATABASE": "SCHEMACHANGE_DEMO_2"}, clear=True)
def test_env_var_with_default_and_environmental_variables_should_return_environmental_variable_value():
    result = JinjaEnvVar.env_var("SF_DATABASE", "SCHEMACHANGE_DEMO")
    assert result == "SCHEMACHANGE_DEMO_2"


@mock.patch.dict(os.environ, {"SF_DATABASE": "SCHEMACHANGE_DEMO_3"}, clear=True)
def test_JinjaEnvVar_with_jinja_template():
    template = jinja2.Template(
        "{{env_var('SF_DATABASE', 'SCHEMACHANGE_DEMO')}}", extensions=[JinjaEnvVar]
    )
    assert template.render() == "SCHEMACHANGE_DEMO_3"
