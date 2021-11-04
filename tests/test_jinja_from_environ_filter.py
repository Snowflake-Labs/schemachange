import json
import os

import pytest
from jinja2 import DictLoader
from jinja2.exceptions import UndefinedError
from schemachange.cli import JinjaTemplateProcessor


def test_from_environ_not_set():
    processor = JinjaTemplateProcessor("", None)

    # overide the default loader
    templates = {"test.sql": "some text {{ myvar | from_environ('MYVAR') }}"}
    processor.override_loader(DictLoader(templates))

    with pytest.raises(UndefinedError) as e:
        context = processor.render("test.sql", None, True)

    assert str(e.value) == "'myvar' is undefined"


def test_from_environ_set():
    processor = JinjaTemplateProcessor("", None)

    # set MYVAR env variable
    os.environ["MYVAR"] = "myvar_from_environment"

    # overide the default loader
    templates = {"test.sql": "some text {{ myvar | from_environ('MYVAR') }}"}
    processor.override_loader(DictLoader(templates))

    context = processor.render("test.sql", None, True)

    # unset MYVAR env variable
    del os.environ["MYVAR"]

    assert context == "some text myvar_from_environment"


def test_from_environ_not_set_default():
    processor = JinjaTemplateProcessor("", None)

    # overide the default loader
    templates = {"test.sql": "some text {{ 'myvar_default' | from_environ('MYVAR') }}"}
    processor.override_loader(DictLoader(templates))

    context = processor.render("test.sql", None, True)

    assert context == "some text myvar_default"


def test_from_environ_not_set_vars():
    processor = JinjaTemplateProcessor("", None)

    # overide the default loader
    templates = {"test.sql": "some text {{ myvar | from_environ('MYVAR') }}"}
    processor.override_loader(DictLoader(templates))

    vars = json.loads('{"myvar" : "myvar_from_vars"}')

    context = processor.render("test.sql", vars, True)

    assert context == "some text myvar_from_vars"
