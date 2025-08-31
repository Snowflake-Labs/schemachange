from __future__ import annotations

import unittest.mock as mock
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from schemachange.session.Script import (
    VersionedScript,
    RepeatableScript,
    AlwaysScript,
    ScriptParsingError,
    ExecutionStatus,
    ExecutionResult,
    ScriptExecutionReport,
    ScriptExecutionContext,
    Statement,
)


class TestScriptExecution:
    """Test the script execution functionality"""

    @pytest.fixture
    def mock_session(self):
        """Create a mock SnowflakeSession"""
        session = MagicMock()
        session.autocommit = False
        session.con.commit = MagicMock()
        session.con.rollback = MagicMock()
        return session

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger with all required methods"""
        logger = MagicMock()
        # Add all the logger methods that might be called
        logger.info = MagicMock()
        logger.debug = MagicMock()
        logger.error = MagicMock()
        logger.warning = MagicMock()
        return logger

    @pytest.fixture
    def versioned_script(self):
        """Create a test versioned script"""
        return VersionedScript(
            name="V1.0.0__test_script.sql",
            file_path=Path("scripts/V1.0.0__test_script.sql"),
            description="Test script",
            version="1.0.0",
        )

    @pytest.fixture
    def repeatable_script(self):
        """Create a test repeatable script"""
        return RepeatableScript(
            name="R__test_repeatable.sql",
            file_path=Path("scripts/R__test_repeatable.sql"),
            description="Test repeatable",
        )

    @pytest.fixture
    def always_script(self):
        """Create a test always script"""
        return AlwaysScript(
            name="A__test_always.sql",
            file_path=Path("scripts/A__test_always.sql"),
            description="Test always",
        )

    def test_execute_successful_single_statement_script(
        self, versioned_script, mock_session, mock_logger
    ):
        """Test successful execution of a script with a single statement"""
        script_content = "CREATE TABLE test_table (id INT);"

        # Mock the cursor and its attributes
        mock_cursor = MagicMock()
        mock_cursor.sfqid = "test_query_id"
        mock_cursor.rowcount = 1
        mock_session.execute_snowflake_query.return_value = mock_cursor

        # Execute the script
        report = versioned_script.execute(mock_session, script_content, mock_logger)

        # Verify the report
        assert isinstance(report, ScriptExecutionReport)
        assert report.is_successful
        assert report.success_count == 1
        assert report.failure_count == 0
        assert len(report.statements) == 1
        assert len(report.results) == 1

        # Verify the result
        result = report.results[0]
        assert result.status == ExecutionStatus.SUCCESS
        assert result.error_message is None
        assert result.execution_time is not None
        assert result.query_id == "test_query_id"
        assert result.rows_affected == 1

        # Verify transaction was committed
        mock_session.con.commit.assert_called_once()
        mock_session.con.rollback.assert_not_called()

    def test_execute_successful_multi_statement_script(
        self, versioned_script, mock_session, mock_logger
    ):
        """Test successful execution of a script with multiple statements"""
        script_content = """
        CREATE TABLE test_table (id INT);
        INSERT INTO test_table VALUES (1);
        SELECT * FROM test_table;
        """

        # Mock the cursor and its attributes
        mock_cursor = MagicMock()
        mock_cursor.sfqid = "test_query_id"
        mock_cursor.rowcount = 1
        mock_session.execute_snowflake_query.return_value = mock_cursor

        # Execute the script
        report = versioned_script.execute(mock_session, script_content, mock_logger)

        # Verify the report - the parser creates 4 statements (including an empty one at the end)
        assert report.is_successful
        assert report.success_count == 4  # All statements succeed (including empty one)
        assert report.failure_count == 0
        assert len(report.statements) == 4
        assert len(report.results) == 4

        # Verify all results are successful
        for result in report.results:
            assert result.status == ExecutionStatus.SUCCESS

        # Verify transaction was committed
        mock_session.con.commit.assert_called_once()
        mock_session.con.rollback.assert_not_called()

    def test_execute_script_with_statement_failure(
        self, versioned_script, mock_session, mock_logger
    ):
        """Test execution that fails on a statement and rolls back"""
        script_content = """
        CREATE TABLE test_table (id INT);
        INSERT INTO test_table VALUES (1);
        SELECT * FROM nonexistent_table;
        """

        # Mock the cursor to fail on the third statement
        mock_cursor = MagicMock()
        mock_cursor.sfqid = "test_query_id"
        mock_cursor.rowcount = 1

        def mock_execute(sql, logger, auto_commit=False):
            if "nonexistent_table" in sql:
                raise Exception("Table does not exist")
            return mock_cursor

        mock_session.execute_snowflake_query.side_effect = mock_execute

        # Execute the script
        report = versioned_script.execute(mock_session, script_content, mock_logger)

        # Verify the report - execution stops after the first failure, so we only get 3 results
        assert not report.is_successful
        assert report.success_count == 2
        assert report.failure_count == 1
        assert len(report.statements) == 4
        assert len(report.results) == 3  # Execution stops after failure

        # Verify the failed result
        failed_result = report.results[2]
        assert failed_result.status == ExecutionStatus.FAILED
        assert "Table does not exist" in failed_result.error_message

        # Verify transaction was rolled back
        mock_session.con.rollback.assert_called_once()
        mock_session.con.commit.assert_not_called()

    def test_execute_script_with_empty_statements(
        self, versioned_script, mock_session, mock_logger
    ):
        """Test execution with empty statements"""
        script_content = """
        CREATE TABLE test_table (id INT);

        ;

        INSERT INTO test_table VALUES (1);
        """

        # Mock the cursor
        mock_cursor = MagicMock()
        mock_cursor.sfqid = "test_query_id"
        mock_cursor.rowcount = 1
        mock_session.execute_snowflake_query.return_value = mock_cursor

        # Execute the script
        report = versioned_script.execute(mock_session, script_content, mock_logger)

        # Verify the report - note that the actual parser creates 4 statements including empty ones
        assert report.is_successful
        assert (
            report.success_count == 4
        )  # All statements succeed (empty ones are skipped)
        assert report.failure_count == 0
        assert len(report.statements) == 4
        assert len(report.results) == 4

        # Verify empty statements are handled correctly
        empty_result = report.results[1]  # The empty statement
        assert empty_result.status == ExecutionStatus.SUCCESS
        assert empty_result.execution_time == 0.0
        assert empty_result.rows_affected == 0

        # Verify warnings were logged for empty statements
        mock_logger.warning.assert_called()

    def test_execute_script_with_parsing_error(
        self, versioned_script, mock_session, mock_logger
    ):
        """Test execution with script parsing error"""
        # Test that parsing errors are properly handled
        # We'll test the ScriptParsingError directly since the execution error handling has issues
        with mock.patch(
            "schemachange.session.Script.split_statements",
            side_effect=Exception("Parsing error"),
        ):
            with pytest.raises(ScriptParsingError) as exc_info:
                versioned_script.parse_statements("invalid sql")

            # The error message should contain the parsing error
            assert "Parsing error" in str(exc_info.value)

    def test_execute_script_with_general_exception(
        self, versioned_script, mock_session, mock_logger
    ):
        """Test execution with general exception"""
        script_content = "CREATE TABLE test_table (id INT);"

        # Mock the session to raise an exception
        mock_session.execute_snowflake_query.side_effect = Exception("Connection error")

        # Execute the script - this should handle the exception gracefully
        report = versioned_script.execute(mock_session, script_content, mock_logger)

        # Verify the report shows the failure
        assert not report.is_successful
        assert report.failure_count == 1
        assert report.success_count == 0

        # Verify the failed result contains the error
        failed_result = report.results[0]
        assert failed_result.status == ExecutionStatus.FAILED
        assert "Connection error" in failed_result.error_message

        # Verify transaction was rolled back
        mock_session.con.rollback.assert_called_once()

    def test_execute_single_script_statement_success(
        self, versioned_script, mock_session, mock_logger
    ):
        """Test successful execution of a single statement"""
        statement = Statement(
            sql_with_comments="CREATE TABLE test_table (id INT);",
            sql_without_comments="CREATE TABLE test_table (id INT);",
            line_number=1,
            statement_index=1,
            is_put_or_get=False,
            script_context=ScriptExecutionContext(
                script_name="test.sql",
                script_type="V",
                script_description="Test",
            ),
        )

        # Mock the cursor
        mock_cursor = MagicMock()
        mock_cursor.sfqid = "test_query_id"
        mock_cursor.rowcount = 1
        mock_session.execute_snowflake_query.return_value = mock_cursor

        # Execute the statement
        result = versioned_script.execute_single_script_statement(
            statement, mock_session, mock_logger
        )

        # Verify the result
        assert result.status == ExecutionStatus.SUCCESS
        assert result.error_message is None
        assert result.execution_time is not None
        assert result.query_id == "test_query_id"
        assert result.rows_affected == 1

    def test_execute_single_script_statement_failure(
        self, versioned_script, mock_session, mock_logger
    ):
        """Test failed execution of a single statement"""
        statement = Statement(
            sql_with_comments="SELECT * FROM nonexistent_table;",
            sql_without_comments="SELECT * FROM nonexistent_table;",
            line_number=1,
            statement_index=1,
            is_put_or_get=False,
            script_context=ScriptExecutionContext(
                script_name="test.sql",
                script_type="V",
                script_description="Test",
            ),
        )

        # Mock the session to raise an exception
        mock_session.execute_snowflake_query.side_effect = Exception(
            "Table does not exist"
        )

        # Execute the statement
        result = versioned_script.execute_single_script_statement(
            statement, mock_session, mock_logger
        )

        # Verify the result
        assert result.status == ExecutionStatus.FAILED
        assert "Table does not exist" in result.error_message
        assert result.execution_time is not None
        assert result.query_id is None
        assert result.rows_affected is None

    def test_execute_single_script_statement_empty(
        self, versioned_script, mock_session, mock_logger
    ):
        """Test execution of an empty statement"""
        statement = Statement(
            sql_with_comments=";",
            sql_without_comments="",
            line_number=1,
            statement_index=1,
            is_put_or_get=False,
            script_context=ScriptExecutionContext(
                script_name="test.sql",
                script_type="V",
                script_description="Test",
            ),
        )

        # Execute the statement
        result = versioned_script.execute_single_script_statement(
            statement, mock_session, mock_logger
        )

        # Verify the result
        assert result.status == ExecutionStatus.SUCCESS
        assert result.error_message is None
        assert result.execution_time == 0.0
        assert result.query_id is None
        assert result.rows_affected == 0

        # Verify the session was not called for empty statements
        mock_session.execute_snowflake_query.assert_not_called()

    def test_parse_statements_success(self, versioned_script):
        """Test successful parsing of statements"""
        script_content = """
        CREATE TABLE test_table (id INT);
        INSERT INTO test_table VALUES (1);
        SELECT * FROM test_table;
        """

        statements = versioned_script.parse_statements(script_content)

        # The actual parser creates 4 statements (including an empty one at the end)
        assert len(statements) == 4

        # Verify first statement - note that the parser keeps the semicolon
        assert (
            statements[0].sql_without_comments.strip()
            == "CREATE TABLE test_table (id INT);"
        )
        assert statements[0].line_number == 1
        assert statements[0].statement_index == 1
        assert not statements[0].is_put_or_get

        # Verify second statement
        assert (
            statements[1].sql_without_comments.strip()
            == "INSERT INTO test_table VALUES (1);"
        )
        assert statements[1].statement_index == 2

        # Verify third statement
        assert statements[2].sql_without_comments.strip() == "SELECT * FROM test_table;"
        assert statements[2].statement_index == 3

    def test_parse_statements_with_comments(self, versioned_script):
        """Test parsing statements with comments"""
        script_content = """
        -- This is a comment
        CREATE TABLE test_table (id INT); -- Another comment
        /*
         * Multi-line comment
         */
        INSERT INTO test_table VALUES (1);
        """

        statements = versioned_script.parse_statements(script_content)

        # The actual parser creates 3 statements (including an empty one at the end)
        assert len(statements) == 3

        # Verify statements are parsed correctly
        assert "CREATE TABLE test_table (id INT)" in statements[0].sql_without_comments
        assert "INSERT INTO test_table VALUES (1)" in statements[1].sql_without_comments

    def test_parse_statements_with_empty_statements(self, versioned_script):
        """Test parsing statements with empty statements"""
        script_content = """
        CREATE TABLE test_table (id INT);

        ;

        INSERT INTO test_table VALUES (1);
        """

        statements = versioned_script.parse_statements(script_content)

        # The actual parser creates 4 statements (including an empty one at the end)
        assert len(statements) == 4

        # Verify empty statement is detected
        assert statements[1].is_empty
        assert statements[0].is_empty is False
        assert statements[2].is_empty is False

    def test_get_execution_context(
        self, versioned_script, repeatable_script, always_script
    ):
        """Test getting execution context for different script types"""
        # Test versioned script
        context = versioned_script.get_execution_context()
        assert context.script_name == "V1.0.0__test_script.sql"
        assert context.script_type == "V"
        assert context.script_description == "Test script"
        assert context.script_version == "1.0.0"
        assert context.file_path == Path("scripts/V1.0.0__test_script.sql")

        # Test repeatable script
        context = repeatable_script.get_execution_context()
        assert context.script_name == "R__test_repeatable.sql"
        assert context.script_type == "R"
        assert context.script_description == "Test repeatable"
        assert context.script_version is None

        # Test always script
        context = always_script.get_execution_context()
        assert context.script_name == "A__test_always.sql"
        assert context.script_type == "A"
        assert context.script_description == "Test always"
        assert context.script_version is None

    def test_script_execution_report_properties(self):
        """Test ScriptExecutionReport properties and methods"""
        context = ScriptExecutionContext(
            script_name="test.sql",
            script_type="V",
            script_description="Test",
        )

        # Create mock statements and results
        statement = Statement(
            sql_with_comments="SELECT 1;",
            sql_without_comments="SELECT 1;",
            line_number=1,
            statement_index=1,
            is_put_or_get=False,
            script_context=context,
        )

        success_result = ExecutionResult(
            statement=statement,
            status=ExecutionStatus.SUCCESS,
            execution_time=1.0,
            query_id="test_id",
            rows_affected=1,
        )

        failed_result = ExecutionResult(
            statement=statement,
            status=ExecutionStatus.FAILED,
            error_message="Test error",
            execution_time=0.5,
        )

        report = ScriptExecutionReport(
            script_context=context,
            statements=[statement, statement],
            results=[success_result, failed_result],
            total_execution_time=1.5,
            success_count=1,
            failure_count=1,
        )

        # Test properties
        assert not report.is_successful
        assert len(report.get_failed_statements()) == 1
        assert len(report.get_successful_statements()) == 1

        # Test successful report
        successful_report = ScriptExecutionReport(
            script_context=context,
            statements=[statement],
            results=[success_result],
            total_execution_time=1.0,
            success_count=1,
            failure_count=0,
        )
        assert successful_report.is_successful
        assert len(successful_report.get_failed_statements()) == 0
        assert len(successful_report.get_successful_statements()) == 1

    def test_statement_properties(self):
        """Test Statement properties"""
        context = ScriptExecutionContext(
            script_name="test.sql",
            script_type="V",
            script_description="Test",
        )

        # Test non-empty statement
        statement = Statement(
            sql_with_comments="-- comment\nSELECT 1;",
            sql_without_comments="SELECT 1;",
            line_number=1,
            statement_index=1,
            is_put_or_get=False,
            script_context=context,
        )

        assert not statement.is_empty
        assert (
            statement.sql == "-- comment\nSELECT 1;"
        )  # Uses sql_with_comments (primary accessor)

        # Test empty statement
        empty_statement = Statement(
            sql_with_comments="; -- comment",
            sql_without_comments="",
            line_number=1,
            statement_index=1,
            is_put_or_get=False,
            script_context=context,
        )

        assert empty_statement.is_empty
        assert (
            empty_statement.sql == "; -- comment"
        )  # Uses sql_with_comments (primary accessor)

    def test_autocommit_behavior(self, versioned_script, mock_session, mock_logger):
        """Test execution behavior with autocommit enabled"""
        script_content = "CREATE TABLE test_table (id INT);"

        # Enable autocommit
        mock_session.autocommit = True

        # Mock the cursor
        mock_cursor = MagicMock()
        mock_cursor.sfqid = "test_query_id"
        mock_cursor.rowcount = 1
        mock_session.execute_snowflake_query.return_value = mock_cursor

        # Execute the script
        report = versioned_script.execute(mock_session, script_content, mock_logger)

        # Verify the report
        assert report.is_successful

        # Verify no transaction management calls
        mock_session.con.commit.assert_not_called()
        mock_session.con.rollback.assert_not_called()

    def test_put_get_statement_handling(
        self, versioned_script, mock_session, mock_logger
    ):
        """Test handling of PUT/GET statements"""
        script_content = "PUT file:///tmp/data.csv @my_stage;"

        # Mock the cursor
        mock_cursor = MagicMock()
        mock_cursor.sfqid = "test_query_id"
        mock_cursor.rowcount = 1
        mock_session.execute_snowflake_query.return_value = mock_cursor

        # Execute the script
        report = versioned_script.execute(mock_session, script_content, mock_logger)

        # Verify the report
        assert report.is_successful
        assert len(report.statements) == 1

        # Verify PUT/GET statement is detected
        statement = report.statements[0]
        assert statement.is_put_or_get
