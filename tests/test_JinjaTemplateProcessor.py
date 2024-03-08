from __future__ import annotations

import json
import os
import pathlib

import pytest
from jinja2 import DictLoader
from jinja2.exceptions import UndefinedError
from schemachange.JinjaTemplateProcessor import JinjaTemplateProcessor


@pytest.fixture()
def processor() -> JinjaTemplateProcessor:
    return JinjaTemplateProcessor(pathlib.Path("."), None)


class TestJinjaTemplateProcessor:
    def test_render_simple_string(self, processor: JinjaTemplateProcessor):
        # override the default loader
        templates = {"test.sql": "some text"}
        processor.override_loader(DictLoader(templates))

        context = processor.render("test.sql", None)

        assert context == "some text"

    def test_render_simple_string_expecting_variable_that_does_not_exist_should_raise_exception(
        self, processor: JinjaTemplateProcessor
    ):
        # overide the default loader
        templates = {"test.sql": "some text {{ myvar }}"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(UndefinedError) as e:
            processor.render("test.sql", None)

        assert str(e.value) == "'myvar' is undefined"

    def test_render_simple_string_expecting_variable(
        self, processor: JinjaTemplateProcessor
    ):
        # overide the default loader
        templates = {"test.sql": "Hello {{ myvar }}!"}
        processor.override_loader(DictLoader(templates))

        variables = json.loads('{"myvar" : "world"}')

        context = processor.render("test.sql", variables)

        assert context == "Hello world!"

    def test_render_from_subfolder(self, tmp_path: pathlib.Path):
        root_folder = tmp_path / "MORE2"

        root_folder.mkdir()
        script_folder = root_folder / "SQL"
        script_folder.mkdir()
        script_file = script_folder / "1.0.0_my_test.sql"
        script_file.write_text("Hello world!")

        processor = JinjaTemplateProcessor(root_folder, None)
        template_path = processor.relpath(script_file)

        context = processor.render(template_path, {})

        assert context == "Hello world!"

    def test_from_environ_not_set(self, processor: JinjaTemplateProcessor):
        # overide the default loader
        templates = {"test.sql": "some text {{ env_var('MYVAR') }}"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert (
            str(e.value)
            == "Could not find environmental variable MYVAR and no default value was provided"
        )

    def test_from_environ_set(self, processor: JinjaTemplateProcessor):
        # set MYVAR env variable
        os.environ["MYVAR"] = "myvar_from_environment"

        # overide the default loader
        templates = {"test.sql": "some text {{ env_var('MYVAR') }}"}
        processor.override_loader(DictLoader(templates))

        context = processor.render("test.sql", None)

        # unset MYVAR env variable
        del os.environ["MYVAR"]

        assert context == "some text myvar_from_environment"

    def test_from_environ_not_set_default(self, processor: JinjaTemplateProcessor):
        # overide the default loader
        templates = {"test.sql": "some text {{ env_var('MYVAR', 'myvar_default') }}"}
        processor.override_loader(DictLoader(templates))

        context = processor.render("test.sql", None)

        assert context == "some text myvar_default"
