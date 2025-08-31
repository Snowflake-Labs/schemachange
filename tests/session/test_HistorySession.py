from __future__ import annotations

from unittest import mock

import pytest
import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.session.HistorySession import HistorySession


@pytest.fixture
def history_session() -> HistorySession:
    change_history_table = ChangeHistoryTable()
    logger = structlog.testing.CapturingLogger()

    with mock.patch("snowflake.connector.connect"):
        with mock.patch(
            "schemachange.session.HistorySession.get_snowflake_identifier_string"
        ):
            # noinspection PyTypeChecker
            return HistorySession(
                user="user",
                account="account",
                role="role",
                warehouse="warehouse",
                schemachange_version="3.6.1.dev",
                application="schemachange",
                change_history_table=change_history_table,
                logger=logger,
            )


class TestHistorySession:
    def test_init_creates_connection_with_correct_parameters(self):
        """Test that HistorySession initializes with correct connection parameters."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            with mock.patch(
                "schemachange.session.HistorySession.get_snowflake_identifier_string"
            ):
                HistorySession(
                    user="test_user",
                    account="test_account",
                    role="test_role",
                    warehouse="test_warehouse",
                    database="test_database",
                    schema="test_schema",
                    schemachange_version="3.6.1.dev",
                    application="schemachange",
                    change_history_table=change_history_table,
                    logger=logger,
                )

                # Verify connection was created with correct parameters
                mock_connect.assert_called_once()
                call_kwargs = mock_connect.call_args[1]
                assert call_kwargs["user"] == "test_user"
                assert call_kwargs["account"] == "test_account"
                assert call_kwargs["role"] == "test_role"
                assert call_kwargs["warehouse"] == "test_warehouse"
                assert call_kwargs["database"] == "test_database"
                assert call_kwargs["schema"] == "test_schema"
                assert call_kwargs["application"] == "schemachange"
                assert (
                    "schemachange_history 3.6.1.dev"
                    in call_kwargs["session_parameters"]["QUERY_TAG"]
                )

    def test_init_with_query_tag(self):
        """Test that HistorySession handles custom query tags correctly."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            with mock.patch(
                "schemachange.session.HistorySession.get_snowflake_identifier_string"
            ):
                HistorySession(
                    user="test_user",
                    account="test_account",
                    schemachange_version="3.6.1.dev",
                    application="schemachange",
                    change_history_table=change_history_table,
                    logger=logger,
                    query_tag="custom_tag",
                )

                call_kwargs = mock_connect.call_args[1]
                assert (
                    "schemachange_history 3.6.1.dev;custom_tag"
                    in call_kwargs["session_parameters"]["QUERY_TAG"]
                )

    def test_execute_query_success(self, history_session):
        """Test successful query execution."""
        mock_cursor = mock.MagicMock()
        history_session.con.cursor.return_value = mock_cursor

        result = history_session.execute_query("SELECT 1", history_session.logger)

        mock_cursor.execute.assert_called_once_with("SELECT 1")
        assert result == mock_cursor

    def test_execute_query_with_autocommit(self, history_session):
        """Test query execution with autocommit enabled."""
        history_session.autocommit = True
        mock_cursor = mock.MagicMock()
        history_session.con.cursor.return_value = mock_cursor

        result = history_session.execute_query("SELECT 1", history_session.logger)

        mock_cursor.execute.assert_called_once_with("SELECT 1")
        # Should not commit when autocommit is True
        history_session.con.commit.assert_not_called()
        assert result == mock_cursor

    def test_execute_query_without_autocommit(self, history_session):
        """Test query execution without autocommit."""
        history_session.autocommit = False
        mock_cursor = mock.MagicMock()
        history_session.con.cursor.return_value = mock_cursor

        result = history_session.execute_query("SELECT 1", history_session.logger)

        mock_cursor.execute.assert_called_once_with("SELECT 1")
        history_session.con.commit.assert_called_once()
        assert result == mock_cursor

    def test_execute_query_with_error(self, history_session):
        """Test query execution with error handling."""
        history_session.autocommit = False
        mock_cursor = mock.MagicMock()
        mock_cursor.execute.side_effect = Exception("Test error")
        history_session.con.cursor.return_value = mock_cursor

        with pytest.raises(Exception, match="Test error"):
            history_session.execute_query("SELECT 1", history_session.logger)

        # Should rollback on error when not in autocommit mode
        history_session.con.rollback.assert_called_once()

    def test_fetch_change_history_metadata_exists(self, history_session):
        """Test fetching change history metadata when table exists."""
        mock_cursor = mock.MagicMock()
        mock_cursor.__iter__.return_value = [["created", "last_altered"]]
        history_session.con.cursor.return_value = mock_cursor

        result = history_session.fetch_change_history_metadata()

        # Verify the method was called and returned expected result
        mock_cursor.execute.assert_called_once()
        assert result == {"created": "created", "last_altered": "last_altered"}

    def test_fetch_change_history_metadata_does_not_exist(self, history_session):
        """Test fetching change history metadata when table doesn't exist."""
        mock_cursor = mock.MagicMock()
        mock_cursor.__iter__.return_value = []
        history_session.con.cursor.return_value = mock_cursor

        result = history_session.fetch_change_history_metadata()

        assert result == {}

    def test_change_history_table_exists_with_creation(self, history_session):
        """Test checking if change history table exists with creation enabled."""
        # Mock fetch_change_history_metadata to return empty (table doesn't exist)
        with mock.patch.object(
            history_session, "fetch_change_history_metadata", return_value={}
        ):
            with mock.patch.object(
                history_session, "change_history_schema_exists", return_value=True
            ):
                with mock.patch.object(
                    history_session, "create_change_history_table"
                ) as mock_create:
                    result = history_session.change_history_table_exists(
                        create_change_history_table=True, dry_run=False
                    )

                    # Should create table and return True
                    assert result is True
                    mock_create.assert_called_once_with(dry_run=False)

    def test_change_history_table_exists_without_creation(self, history_session):
        """Test checking if change history table exists without creation."""
        # Mock fetch_change_history_metadata to return empty (table doesn't exist)
        with mock.patch.object(
            history_session, "fetch_change_history_metadata", return_value={}
        ):
            with pytest.raises(ValueError, match="Unable to find change history table"):
                history_session.change_history_table_exists(
                    create_change_history_table=False, dry_run=False
                )

    def test_change_history_table_exists_dry_run(self, history_session):
        """Test checking if change history table exists in dry run mode."""
        # Mock fetch_change_history_metadata to return empty (table doesn't exist)
        with mock.patch.object(
            history_session, "fetch_change_history_metadata", return_value={}
        ):
            with mock.patch.object(
                history_session, "change_history_schema_exists", return_value=True
            ):
                with mock.patch.object(
                    history_session, "create_change_history_table"
                ) as mock_create:
                    result = history_session.change_history_table_exists(
                        create_change_history_table=True, dry_run=True
                    )

                    # Should return False in dry run mode even with creation enabled
                    assert result is False
                    mock_create.assert_called_once_with(dry_run=True)

    def test_fetch_versioned_scripts(self, history_session):
        """Test fetching versioned scripts from change history."""
        mock_cursor = mock.MagicMock()
        mock_cursor.__iter__.return_value = [
            ["V1.0.0__script1.sql", "script1.sql", "checksum1"],
            ["V1.0.1__script2.sql", "script2.sql", "checksum2"],
        ]
        history_session.con.cursor.return_value = mock_cursor

        change_history, max_published_version = (
            history_session.fetch_versioned_scripts()
        )

        # Verify the method was called and returned expected result
        mock_cursor.execute.assert_called_once()
        assert len(change_history) == 2
        assert max_published_version == "V1.0.0__script1.sql"

    def test_fetch_repeatable_scripts(self, history_session):
        """Test fetching repeatable scripts from change history."""
        mock_cursor = mock.MagicMock()
        mock_cursor.__iter__.return_value = [
            ["R__script1.sql", "checksum1"],
            ["R__script2.sql", "checksum2"],
        ]
        history_session.con.cursor.return_value = mock_cursor

        result = history_session.fetch_repeatable_scripts()

        # Verify the method was called and returned expected result
        mock_cursor.execute.assert_called_once()
        assert result == {
            "R__script1.sql": ["checksum1"],
            "R__script2.sql": ["checksum2"],
        }

    def test_insert_change_record(self, history_session):
        """Test inserting a change history record."""
        mock_cursor = mock.MagicMock()
        history_session.con.cursor.return_value = mock_cursor

        history_session.insert_change_record(
            version="V1.0.0",
            description="Test script",
            script_name="V1.0.0__test.sql",
            script_type="V",
            checksum="abc123",
            execution_time=1,
            status="SUCCESS",
            installed_by="test_user",
            logger=history_session.logger,
        )

        # Verify the method was called
        mock_cursor.execute.assert_called_once()
        actual_query = mock_cursor.execute.call_args[0][0]
        # Verify it's an INSERT statement
        assert "INSERT INTO" in actual_query
        assert "V1.0.0" in actual_query
        assert "Test script" in actual_query

    def test_del_closes_connection(self, history_session):
        """Test that __del__ properly closes the connection."""
        history_session.__del__()
        history_session.con.close.assert_called_once()
