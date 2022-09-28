import json
import os

import pytest
from jinja2 import DictLoader

from schemachange.cli import JinjaTemplateProcessor


def test_from_environ_not_set():
    processor = JinjaTemplateProcessor("", None)

    # overide the default loader
    templates = {"test.sql": "some text {{ env_var('MYVAR') }}"}
    processor.override_loader(DictLoader(templates))

    with pytest.raises(ValueError) as e:
        context = processor.render("test.sql", None, True)

    assert str(e.value) == "Could not find environmental variable MYVAR and no default value was provided"


def test_from_environ_set():
    processor = JinjaTemplateProcessor("", None)

    # set MYVAR env variable
    os.environ["MYVAR"] = "myvar_from_environment"

    # overide the default loader
    templates = {"test.sql": "some text {{ env_var('MYVAR') }}"}
    processor.override_loader(DictLoader(templates))

    context = processor.render("test.sql", None, True)

    # unset MYVAR env variable
    del os.environ["MYVAR"]

    assert context == "some text myvar_from_environment"


def test_from_environ_not_set_default():
    processor = JinjaTemplateProcessor("", None)

    # overide the default loader
    templates = {"test.sql": "some text {{ env_var('MYVAR', 'myvar_default') }}"}
    processor.override_loader(DictLoader(templates))

    context = processor.render("test.sql", None, True)

    assert context == "some text myvar_default"
