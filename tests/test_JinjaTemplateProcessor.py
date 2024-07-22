import json
import pathlib

import pytest
from jinja2 import DictLoader
from jinja2.exceptions import UndefinedError
from schemachange.cli import JinjaTemplateProcessor


def test_JinjaTemplateProcessor_render_simple_string():
    processor = JinjaTemplateProcessor("", None)

    # overide the default loader
    templates = {"test.sql": "some text"}
    processor.override_loader(DictLoader(templates))

    context = processor.render("test.sql", None, True)

    assert context == "some text"


def test_JinjaTemplateProcessor_render_simple_string_expecting_variable_that_does_not_exist_should_raise_exception():
    processor = JinjaTemplateProcessor("", None)

    # overide the default loader
    templates = {"test.sql": "some text {{ myvar }}"}
    processor.override_loader(DictLoader(templates))

    with pytest.raises(UndefinedError) as e:
        processor.render("test.sql", None, True)

    assert str(e.value) == "'myvar' is undefined"


def test_JinjaTemplateProcessor_render_simple_string_expecting_variable():
    processor = JinjaTemplateProcessor("", None)

    # overide the default loader
    templates = {"test.sql": "Hello {{ myvar }}!"}
    processor.override_loader(DictLoader(templates))

    vars = json.loads('{"myvar" : "world"}')

    context = processor.render("test.sql", vars, True)

    assert context == "Hello world!"


def test_JinjaTemplateProcessor_render_from_subfolder(tmp_path: pathlib.Path):
    root_folder = tmp_path / "MORE2"

    root_folder.mkdir()
    script_folder = root_folder / "SQL"
    script_folder.mkdir()
    script_file = script_folder / "1.0.0_my_test.sql"
    script_file.write_text("Hello world!")

    processor = JinjaTemplateProcessor(str(root_folder), None)
    template_path = processor.relpath(str(script_file))

    context = processor.render(template_path, {}, True)

    assert context == "Hello world!"
