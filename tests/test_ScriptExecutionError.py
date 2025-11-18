"""Tests for ScriptExecutionError exception class."""

from pathlib import Path

import pytest

from schemachange.ScriptExecutionError import ScriptExecutionError


class TestScriptExecutionError:
    """Test cases for ScriptExecutionError."""

    def test_basic_error_creation(self):
        """Test creating a basic ScriptExecutionError."""
        error = ScriptExecutionError(
            script_name="V1.0.0__test.sql",
            script_path=Path("/path/to/script.sql"),
            script_type="V",
            error_message="Column 'foo' does not exist",
        )

        assert error.script_name == "V1.0.0__test.sql"
        assert error.script_path == Path("/path/to/script.sql")
        assert error.script_type == "V"
        assert error.error_message == "Column 'foo' does not exist"
        assert error.sql_error_code is None
        assert error.sql_state is None
        assert error.query is None
        assert error.original_exception is None

    def test_error_with_sql_details(self):
        """Test creating an error with SQL error code and state."""
        error = ScriptExecutionError(
            script_name="R__always_run.sql",
            script_path=Path("/scripts/R__always_run.sql"),
            script_type="R",
            error_message="SQL compilation error",
            sql_error_code=2003,
            sql_state="42S02",
        )

        assert error.sql_error_code == 2003
        assert error.sql_state == "42S02"

    def test_error_with_query(self):
        """Test creating an error with the failing query."""
        query = "SELECT * FROM non_existent_table"
        error = ScriptExecutionError(
            script_name="A__test.sql",
            script_path=Path("/scripts/A__test.sql"),
            script_type="A",
            error_message="Table does not exist",
            query=query,
        )

        assert error.query == query

    def test_error_with_original_exception(self):
        """Test creating an error with an original exception."""
        original = ValueError("Original error")
        error = ScriptExecutionError(
            script_name="V1.0.0__test.sql",
            script_path=Path("/path/to/script.sql"),
            script_type="V",
            error_message="Wrapped error",
            original_exception=original,
        )

        assert error.original_exception is original

    def test_error_message_format(self):
        """Test that the error message is formatted correctly."""
        error = ScriptExecutionError(
            script_name="V1.0.0__test.sql",
            script_path=Path("/path/to/script.sql"),
            script_type="V",
            error_message="Test error",
        )

        expected_message = "Failed to execute V script 'V1.0.0__test.sql': Test error"
        assert str(error) == expected_message

    def test_get_structured_error(self):
        """Test get_structured_error returns correct dictionary."""
        error = ScriptExecutionError(
            script_name="V1.0.0__test.sql",
            script_path=Path("/path/to/script.sql"),
            script_type="V",
            error_message="Test error",
            sql_error_code=2003,
            sql_state="42S02",
        )

        structured = error.get_structured_error()

        assert structured == {
            "script_name": "V1.0.0__test.sql",
            "script_path": "/path/to/script.sql",
            "script_type": "V",
            "error_message": "Test error",
            "sql_error_code": 2003,
            "sql_state": "42S02",
        }

    def test_get_structured_error_without_sql_details(self):
        """Test get_structured_error when SQL details are None."""
        error = ScriptExecutionError(
            script_name="A__test.sql",
            script_path=Path("/scripts/A__test.sql"),
            script_type="A",
            error_message="Generic error",
        )

        structured = error.get_structured_error()

        assert structured["sql_error_code"] is None
        assert structured["sql_state"] is None

    def test_error_can_be_raised(self):
        """Test that ScriptExecutionError can be raised and caught."""
        with pytest.raises(ScriptExecutionError) as exc_info:
            raise ScriptExecutionError(
                script_name="V1.0.0__test.sql",
                script_path=Path("/path/to/script.sql"),
                script_type="V",
                error_message="Test error",
            )

        error = exc_info.value
        assert error.script_name == "V1.0.0__test.sql"
        assert "Test error" in str(error)

    def test_error_chaining(self):
        """Test that error chaining works correctly."""
        original = ValueError("Original error")

        with pytest.raises(ScriptExecutionError) as exc_info:
            try:
                raise original
            except ValueError as e:
                raise ScriptExecutionError(
                    script_name="V1.0.0__test.sql",
                    script_path=Path("/path/to/script.sql"),
                    script_type="V",
                    error_message="Wrapped error",
                    original_exception=e,
                ) from e

        error = exc_info.value
        assert error.original_exception is original
        assert error.__cause__ is original
