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

    def test_render_ignores_jinja_when_marker_present(self, processor: JinjaTemplateProcessor):
        templates = {"test.sql": "-- schemachange-no-jinja\nselect '{{ should_ignore }}'"}
        processor.override_loader(DictLoader(templates))

        context = processor.render("test.sql", {"should_ignore": "replacement"})

        assert context == "-- schemachange-no-jinja\nselect '{{ should_ignore }}'"

    # ============================================================
    # Empty content validation tests - issue #258
    # ============================================================

    def test_render_empty_content_only_whitespace_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that rendering only whitespace raises ValueError"""
        templates = {"test.sql": "   \n\t  \n   "}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "rendered to empty content" in str(e.value)
        assert "test.sql" in str(e.value)

    def test_render_empty_content_only_comments_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that rendering only SQL comments raises ValueError"""
        templates = {"test.sql": "-- This is a comment\n-- Another comment\n"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "contains only comments" in str(e.value)

    def test_render_empty_content_only_semicolon_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that rendering only semicolon raises ValueError.

        After semicolon stripping, content becomes empty.
        """
        templates = {"test.sql": ";"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "rendered to empty content" in str(e.value)

    def test_render_empty_content_whitespace_and_semicolon_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that rendering whitespace + semicolon raises ValueError.

        After whitespace strip and semicolon strip, content becomes empty.
        """
        templates = {"test.sql": "  \n\t  ;  \n"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "rendered to empty content" in str(e.value)

    def test_render_empty_content_false_jinja_conditional_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that all false conditionals result in empty content error"""
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

        assert "rendered to empty content" in str(e.value)

    def test_render_empty_content_multiline_comment_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that rendering only multi-line comments raises ValueError"""
        templates = {"test.sql": "/* This is a \nmulti-line comment */"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "contains only comments" in str(e.value)

    def test_render_empty_content_mixed_comments_should_raise_error(self, processor: JinjaTemplateProcessor):
        """Test that mixed comment types without SQL raises ValueError"""
        templates = {"test.sql": "-- Single line\n/* Multi-line */\n-- Another line"}
        processor.override_loader(DictLoader(templates))

        with pytest.raises(ValueError) as e:
            processor.render("test.sql", None)

        assert "contains only comments" in str(e.value)

    # ============================================================
    # Trailing semicolon stripping tests - issue #417
    # ============================================================

    def test_render_strips_trailing_semicolon(self, processor: JinjaTemplateProcessor):
        """Test that trailing semicolon is stripped for checksum stability.

        Schemachange strips the final trailing semicolon before computing checksums.
        This ensures checksums remain stable regardless of whether users include
        a trailing semicolon in their scripts.
        """
        templates = {"test.sql": "CREATE TABLE foo (id INT);"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        assert result == "CREATE TABLE foo (id INT)"
        assert not result.endswith(";")

    def test_render_valid_sql_with_inline_comment_passes_through(self, processor: JinjaTemplateProcessor):
        """Test that valid SQL with inline comment passes through"""
        templates = {"test.sql": "SELECT 1 /* inline comment */ FROM dual"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        assert result == "SELECT 1 /* inline comment */ FROM dual"

    def test_render_trailing_comment_after_semicolon_unchanged(self, processor: JinjaTemplateProcessor):
        """Test that SQL with trailing comment AFTER semicolon passes through render() unchanged.

        Issue #414: render() should NOT modify content for checksum stability.
        The trailing comment fix is applied by prepare_for_execution() instead.
        """
        templates = {"test.sql": "CREATE TABLE foo (id INT);\n-- Author: John Doe"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # render() should NOT append SELECT 1; - that's done by prepare_for_execution()
        assert result == "CREATE TABLE foo (id INT);\n-- Author: John Doe"
        assert "SELECT 1; -- schemachange: trailing comment fix" not in result

    def test_render_multistatement_sql_passes_through(self, processor: JinjaTemplateProcessor):
        """Test that multi-statement SQL passes through unchanged"""
        templates = {"test.sql": "DROP VIEW IF EXISTS foo;\nCREATE VIEW foo AS SELECT * FROM bar"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        assert result == "DROP VIEW IF EXISTS foo;\nCREATE VIEW foo AS SELECT * FROM bar"

    def test_render_sql_with_jinja_conditional_should_succeed(self, processor: JinjaTemplateProcessor):
        """Test that valid content with Jinja conditionals works correctly"""
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

    # ============================================================
    # Trailing comment handling tests - issue #258, #406
    # Demo files: A__trailing_comment_after_semicolon.sql,
    #             A__comment_before_semicolon.sql,
    #             A__inline_comment_with_semicolon.sql
    # ============================================================

    def test_render_comment_before_semicolon_unchanged(self, processor: JinjaTemplateProcessor):
        """Test that comment BEFORE semicolon passes through unchanged.

        Pattern: SQL\n-- comment\n;
        This is valid Snowflake syntax - the ; terminates everything including comments.
        No modification needed.
        """
        templates = {"test.sql": "SELECT 1\n-- comment before semicolon\n;"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # Trailing semicolon is stripped
        assert result == "SELECT 1\n-- comment before semicolon\n"
        assert "SELECT 1; -- schemachange" not in result

    def test_render_inline_comment_with_semicolon_unchanged(self, processor: JinjaTemplateProcessor):
        """Test that inline comment on same line as semicolon passes through unchanged.

        Pattern: SQL; -- comment
        This is valid Snowflake syntax - nothing comes after the semicolon.
        No modification needed.
        """
        templates = {"test.sql": "SELECT 1; -- inline comment"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # No modification - inline comment on same line as ;
        assert result == "SELECT 1; -- inline comment"
        assert "SELECT 1; -- schemachange" not in result

    def test_render_multiline_trailing_comment_unchanged(self, processor: JinjaTemplateProcessor):
        """Test that multi-line block comment after semicolon passes through render() unchanged."""
        templates = {"test.sql": "CREATE TABLE bar (id INT);\n/* Metadata\nblock */"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # render() should NOT modify - prepare_for_execution() handles this
        assert result == "CREATE TABLE bar (id INT);\n/* Metadata\nblock */"
        assert "SELECT 1; -- schemachange: trailing comment fix" not in result

    def test_render_multiple_trailing_comments_unchanged(self, processor: JinjaTemplateProcessor):
        """Test that multiple trailing comments after semicolon passes through render() unchanged."""
        templates = {"test.sql": "SELECT 1;\n-- comment 1\n-- comment 2\n-- comment 3"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # render() should NOT modify - prepare_for_execution() handles this
        assert result == "SELECT 1;\n-- comment 1\n-- comment 2\n-- comment 3"
        assert "SELECT 1; -- schemachange: trailing comment fix" not in result

    def test_render_no_semicolon_with_trailing_comment_unchanged(self, processor: JinjaTemplateProcessor):
        """Test that SQL without semicolon and trailing comment passes through unchanged.

        When there's no semicolon, Snowflake executes the whole thing as one statement.
        The comment is part of the statement - no modification needed.
        """
        templates = {"test.sql": "SELECT 1\n-- trailing comment"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # No semicolon, so no modification
        assert result == "SELECT 1\n-- trailing comment"
        assert "SELECT 1; -- schemachange" not in result

    def test_render_strips_whitespace_and_trailing_semicolon(self, processor: JinjaTemplateProcessor):
        """Test that both trailing whitespace and semicolon are stripped.

        Trailing whitespace is stripped first, then trailing semicolon.
        This normalizes scripts for consistent checksum computation.
        """
        templates = {"test.sql": "SELECT 1;\n\n\n"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        assert result == "SELECT 1"
        assert "SELECT 1; -- schemachange" not in result

    def test_render_semicolon_in_comment_unchanged(self, processor: JinjaTemplateProcessor):
        """Test that render() passes through content unchanged even with semicolons in comments.

        Issue #414: render() should NOT modify content for checksum stability.
        """
        templates = {
            "test.sql": """CREATE TABLE foo (id INT);
-- This comment mentions SELECT 1; but it's in a comment
-- Another comment with semicolon; here"""
        }
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # render() should NOT modify content
        assert "SELECT 1; -- schemachange: trailing comment fix" not in result
        assert "CREATE TABLE foo (id INT);" in result

    def test_render_semicolon_in_block_comment_unchanged(self, processor: JinjaTemplateProcessor):
        """Test that render() passes through content unchanged with semicolons in block comments."""
        templates = {
            "test.sql": """SELECT * FROM bar;
/* This block comment has SELECT 1; inside it */"""
        }
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        # render() should NOT modify content
        assert "SELECT 1; -- schemachange: trailing comment fix" not in result
        assert "SELECT * FROM bar;" in result

    # ============================================================
    # UTF-8 BOM handling tests - issue #250
    # ============================================================

    def test_render_strips_utf8_bom_character(self, processor: JinjaTemplateProcessor):
        """Test that UTF-8 BOM character is automatically stripped"""
        templates = {"test.sql": "\ufeffSELECT 1 FROM dual"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        assert not result.startswith("\ufeff")
        assert result == "SELECT 1 FROM dual"

    def test_render_strips_utf8_bom_with_multiline_sql(self, processor: JinjaTemplateProcessor):
        """Test that UTF-8 BOM is stripped from multi-line SQL"""
        templates = {"test.sql": "\ufeff-- Comment\nCREATE TABLE foo (id INT);\nSELECT * FROM foo"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        assert not result.startswith("\ufeff")
        assert "-- Comment" in result
        assert "CREATE TABLE foo (id INT)" in result

    def test_render_handles_bom_in_middle_of_file(self, processor: JinjaTemplateProcessor):
        """Test that BOM in middle of file is not stripped - only leading BOM"""
        templates = {"test.sql": "SELECT '\ufeff' AS bom_char FROM dual"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        assert not result.startswith("\ufeff")
        assert "'\ufeff'" in result  # BOM inside the SQL string should remain

    # ============================================================
    # prepare_for_execution() tests - issue #414
    # Two-phase render: render() for checksum, prepare_for_execution() for Snowflake
    # ============================================================

    def test_prepare_for_execution_appends_select1_for_trailing_comment(self, processor: JinjaTemplateProcessor):
        """Test that prepare_for_execution() appends SELECT 1; for trailing comments.

        Issue #258, #406: Snowflake's execute_string() sees content after ; as a new
        statement. If it's only comments, Snowflake strips them and gets empty string.

        Issue #414: This fix is now applied in prepare_for_execution(), not render(),
        to maintain checksum stability.
        """
        content = "CREATE TABLE foo (id INT);\n-- Author: John Doe"

        result = processor.prepare_for_execution(content, "test.sql")

        assert "CREATE TABLE foo (id INT);" in result
        assert "-- Author: John Doe" in result
        assert "SELECT 1; -- schemachange: trailing comment fix" in result

    def test_prepare_for_execution_appends_select1_for_multiline_comment(self, processor: JinjaTemplateProcessor):
        """Test that prepare_for_execution() handles multi-line block comments."""
        content = "CREATE TABLE bar (id INT);\n/* Metadata\nblock */"

        result = processor.prepare_for_execution(content, "test.sql")

        assert "CREATE TABLE bar (id INT);" in result
        assert "/* Metadata\nblock */" in result
        assert "SELECT 1; -- schemachange: trailing comment fix" in result

    def test_prepare_for_execution_appends_select1_for_multiple_trailing_comments(
        self, processor: JinjaTemplateProcessor
    ):
        """Test that prepare_for_execution() handles multiple trailing comments."""
        content = "SELECT 1;\n-- comment 1\n-- comment 2\n-- comment 3"

        result = processor.prepare_for_execution(content, "test.sql")

        assert "SELECT 1;" in result
        assert "-- comment 1" in result
        assert "SELECT 1; -- schemachange: trailing comment fix" in result

    def test_prepare_for_execution_unchanged_for_inline_comment(self, processor: JinjaTemplateProcessor):
        """Test that prepare_for_execution() doesn't modify inline comments on same line as ;"""
        content = "SELECT 1; -- inline comment"

        result = processor.prepare_for_execution(content, "test.sql")

        assert result == "SELECT 1; -- inline comment"
        assert "SELECT 1; -- schemachange" not in result

    def test_prepare_for_execution_unchanged_for_no_trailing_content(self, processor: JinjaTemplateProcessor):
        """Test that prepare_for_execution() doesn't modify SQL ending with just semicolon."""
        content = "CREATE TABLE foo (id INT);"

        result = processor.prepare_for_execution(content, "test.sql")

        assert result == "CREATE TABLE foo (id INT);"
        assert "SELECT 1; -- schemachange" not in result

    def test_prepare_for_execution_skips_cli_scripts(self, processor: JinjaTemplateProcessor):
        """Test that prepare_for_execution() doesn't modify CLI scripts."""
        content = "steps:\n  - command: echo hello"

        result = processor.prepare_for_execution(content, "test.cli.yml")

        assert result == content
        assert "SELECT 1;" not in result

    def test_prepare_for_execution_handles_semicolon_in_comment(self, processor: JinjaTemplateProcessor):
        """Test that semicolons inside comments are correctly ignored."""
        content = """CREATE TABLE foo (id INT);
-- This comment mentions SELECT 1; but it's in a comment
-- Another comment with semicolon; here"""

        result = processor.prepare_for_execution(content, "test.sql")

        # The real last semicolon is after "CREATE TABLE foo (id INT)"
        # The trailing comments should trigger SELECT 1; append
        assert "SELECT 1; -- schemachange: trailing comment fix" in result

    def test_two_phase_render_checksum_stability(self, processor: JinjaTemplateProcessor):
        """Test that render() output is stable for checksum computation.

        Issue #414: This is a regression test to ensure checksums don't change
        between schemachange versions. The content returned by render() should
        NOT include any execution-time transformations.
        """
        templates = {"test.sql": "SELECT 1;\n-- trailing comment"}
        processor.override_loader(DictLoader(templates))

        # render() should return content without modification (except semicolon strip)
        rendered = processor.render("test.sql", None)
        assert rendered == "SELECT 1;\n-- trailing comment"
        assert "schemachange" not in rendered

        # prepare_for_execution() should add the fix
        executable = processor.prepare_for_execution(rendered, "test.sql")
        assert "SELECT 1; -- schemachange: trailing comment fix" in executable

        # Checksum should be computed on rendered content, not executable
        import hashlib

        checksum = hashlib.sha224(rendered.encode()).hexdigest()
        # This checksum should be stable across versions
        assert checksum == hashlib.sha224(b"SELECT 1;\n-- trailing comment").hexdigest()

    # ============================================================
    # Checksum stability regression tests - issue #417
    # ============================================================

    def test_render_produces_stable_checksums(self, processor: JinjaTemplateProcessor):
        """Verify checksums remain stable for common SQL patterns.

        If checksums change, existing deployments will show "checksum has drifted"
        warnings or re-execute R-scripts. These values must remain constant.
        """
        import hashlib

        test_cases = [
            ("-- Test\nSELECT 1;", "e129d259291ecc5ae22313776fd114d035fc8d61a6445d93138c7a64"),
            ("-- Test\nSELECT 1", "e129d259291ecc5ae22313776fd114d035fc8d61a6445d93138c7a64"),
        ]

        for sql, expected_checksum in test_cases:
            templates = {"test.sql": sql}
            processor.override_loader(DictLoader(templates))
            result = processor.render("test.sql", None)
            actual = hashlib.sha224(result.encode()).hexdigest()
            assert actual == expected_checksum, (
                f"Checksum changed for '{sql}': got {actual}, expected {expected_checksum}"
            )

    @pytest.mark.parametrize(
        "sql,expected,semicolon_count",
        [
            ("SELECT 1;", "SELECT 1", 0),
            ("SELECT 1;\nSELECT 2;", "SELECT 1;\nSELECT 2", 1),
            ("SELECT 1;\nSELECT 2;\nSELECT 3;", "SELECT 1;\nSELECT 2;\nSELECT 3", 2),
            ("SELECT 1;\nSELECT 2", "SELECT 1;\nSELECT 2", 1),
            ("SELECT 1;\n-- comment", "SELECT 1;\n-- comment", 1),
        ],
    )
    def test_render_strips_only_final_trailing_semicolon(
        self, processor: JinjaTemplateProcessor, sql, expected, semicolon_count
    ):
        """Test that only the final trailing semicolon is stripped.

        Internal semicolons between statements must be preserved.
        """
        templates = {"test.sql": sql}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        assert result == expected
        assert result.count(";") == semicolon_count

    def test_render_handles_bom_and_trailing_semicolon(self, processor: JinjaTemplateProcessor):
        """Test that BOM removal and semicolon stripping work together."""
        templates = {"test.sql": "\ufeffSELECT 1;"}
        processor.override_loader(DictLoader(templates))

        result = processor.render("test.sql", None)

        assert not result.startswith("\ufeff")
        assert not result.endswith(";")
        assert result == "SELECT 1"
