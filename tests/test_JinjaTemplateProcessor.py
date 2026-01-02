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

    def test_render_simple_string_expecting_variable(self, processor: JinjaTemplateProcessor):
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

        assert str(e.value) == "Could not find environmental variable MYVAR and no default value was provided"

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

    def test_render_empty_content_only_whitespace_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that rendering only whitespace raises ValueError - issue #258"""
        templates = {"test.sql": "   \n\t  \n   "}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "rendered to empty SQL content" in str(e.value)
        assert "test.sql" in str(e.value)

    def test_render_empty_content_only_comments_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that rendering only SQL comments raises ValueError - issue #258

        When Snowflake connector receives comment-only content, it strips comments
        and tries to execute an empty string, causing "Empty SQL Statement" error.
        We catch this proactively with better error messaging.
        """
        templates = {"test.sql": "-- This is a comment\n-- Another comment\n"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        error_message = str(e.value)
        assert "contains only SQL comments" in error_message
        assert "To fix:" in error_message
        assert "Add actual SQL statements" in error_message

    def test_render_empty_content_only_semicolon_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that rendering only semicolon raises ValueError - issue #258"""
        templates = {"test.sql": ";"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "rendered to empty SQL content" in str(e.value)

    def test_render_empty_content_whitespace_and_semicolon_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that rendering whitespace + semicolon raises ValueError - issue #258"""
        templates = {"test.sql": "  \n\t  ;  \n"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "rendered to empty SQL content" in str(e.value)

    def test_render_empty_content_false_jinja_conditional_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that all false conditionals result in empty content error - issue #258"""
        templates = {
            "test.sql": """
            {% if deploy_env == 'prod' %}
            CREATE TABLE my_table (id INT);
            {% endif %}
            """
        }
        processor.override_loader(DictLoader(templates))

        # deploy_env is not 'prod', so conditional evaluates to false
        variables = {"deploy_env": "dev"}

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", variables)

        assert "rendered to empty SQL content" in str(e.value)
        assert "All Jinja conditional blocks evaluate to false" in str(e.value)

    def test_render_empty_content_provides_helpful_error_message(self, processor: JinjaTemplateProcessor):
        """Test that error message includes helpful debugging info - issue #258"""
        templates = {
            "test.sql": """
            {% if feature_enabled %}
            SELECT * FROM table;
            {% endif %}
            """
        }
        processor.override_loader(DictLoader(templates))

        variables = {"feature_enabled": False}

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", variables)

        error_message = str(e.value)
        # Check that error message contains helpful information
        assert "rendered to empty SQL content" in error_message
        assert "This can happen when:" in error_message
        assert "Raw content preview" in error_message
        assert "Provided variables:" in error_message
        assert "feature_enabled" in error_message

    def test_render_valid_content_with_jinja_conditional_should_succeed(self, processor: JinjaTemplateProcessor):
        """Test that valid content with Jinja conditionals works correctly - issue #258"""
        templates = {
            "test.sql": """
            {% if deploy_env == 'prod' %}
            CREATE TABLE prod_table (id INT);
            {% else %}
            CREATE TABLE dev_table (id INT);
            {% endif %}
            """
        }
        processor.override_loader(DictLoader(templates))

        variables = {"deploy_env": "dev"}
        context = processor.render("test.sql", variables)

        assert "CREATE TABLE dev_table (id INT)" in context
        assert "prod_table" not in context

    def test_render_empty_content_multiline_comment_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that rendering only multi-line comments raises ValueError - issue #258"""
        templates = {"test.sql": "/* This is a \nmulti-line comment */"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "contains only SQL comments" in str(e.value)

    def test_render_empty_content_mixed_comments_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that mixed comment types without SQL raises ValueError - issue #258"""
        templates = {"test.sql": "-- Single line\n/* Multi-line */\n-- Another line"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "contains only SQL comments" in str(e.value)

    def test_render_valid_sql_with_trailing_comment_appends_noop(self, processor: JinjaTemplateProcessor):
        """Test that valid SQL with trailing comment gets no-op statement appended - issue #258

        When scripts end with comments, Snowflake connector may strip them causing
        "Empty SQL Statement" error. We append SELECT 1 to ensure there's always
        a valid statement after comments, preserving metadata.
        """
        templates = {"test.sql": "CREATE TABLE foo (id INT);\n-- Author: John Doe\n-- Ticket: JIRA-123"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # Original SQL is preserved
        assert "CREATE TABLE foo (id INT)" in result
        # Metadata comments are preserved
        assert "Author: John Doe" in result
        assert "Ticket: JIRA-123" in result
        # No-op statement is appended
        assert "SELECT 1; -- schemachange: no-op statement" in result

    def test_render_valid_sql_with_inline_comment_should_succeed(self, processor: JinjaTemplateProcessor):
        """Test that valid SQL with inline comment works - issue #258"""
        templates = {"test.sql": "SELECT 1 /* inline comment */ FROM dual"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)
        assert "SELECT 1" in result
        assert "FROM dual" in result
        # Should NOT append SELECT 1 because last line is not a comment
        assert result.count("SELECT 1") == 1  # Only the original SELECT 1

    def test_render_valid_sql_without_trailing_comment_unchanged(self, processor: JinjaTemplateProcessor):
        """Test that valid SQL without trailing comment passes through unchanged - issue #258"""
        templates = {"test.sql": "DROP VIEW IF EXISTS foo;\nCREATE VIEW foo AS SELECT * FROM bar"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # Content is unchanged - no SELECT 1 appended
        assert result == "DROP VIEW IF EXISTS foo;\nCREATE VIEW foo AS SELECT * FROM bar"
        assert "SELECT 1" not in result

    def test_render_valid_sql_with_trailing_multiline_comment_appends_noop(self, processor: JinjaTemplateProcessor):
        """Test that valid SQL ending with multi-line comment gets no-op appended - issue #258"""
        templates = {"test.sql": "CREATE TABLE bar (id INT);\n/* Metadata block */"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        assert "CREATE TABLE bar (id INT)" in result
        assert "/* Metadata block */" in result
        assert "SELECT 1; -- schemachange: no-op statement" in result

    def test_render_strips_utf8_bom_character(self, processor: JinjaTemplateProcessor):
        """Test that UTF-8 BOM character is automatically stripped - issue #250"""
        # \ufeff is the UTF-8 BOM (Byte Order Mark) character
        templates = {"test.sql": "\ufeffSELECT 1 FROM dual"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # BOM should be stripped
        assert not result.startswith("\ufeff")
        assert result == "SELECT 1 FROM dual"

    def test_render_strips_utf8_bom_with_multiline_sql(self, processor: JinjaTemplateProcessor):
        """Test that UTF-8 BOM is stripped from multi-line SQL - issue #250"""
        templates = {"test.sql": "\ufeff-- Comment\nCREATE TABLE foo (id INT);\nSELECT * FROM foo"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # BOM should be stripped, rest preserved
        assert not result.startswith("\ufeff")
        assert "-- Comment" in result
        assert "CREATE TABLE foo (id INT)" in result
        assert "SELECT * FROM foo" in result

    def test_render_handles_bom_in_middle_of_file(self, processor: JinjaTemplateProcessor):
        """Test that BOM in middle of file is not stripped - only leading BOM - issue #250"""
        # BOM should only be stripped at the start of the file
        templates = {"test.sql": "SELECT '\ufeff' AS bom_char FROM dual"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # Leading BOM removed but BOM in SQL string preserved
        assert not result.startswith("\ufeff")
        assert "'\ufeff'" in result  # BOM inside the SQL string should remain
