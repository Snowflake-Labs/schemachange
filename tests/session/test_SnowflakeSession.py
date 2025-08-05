from __future__ import annotations

from unittest import mock
from pathlib import Path

import pytest
import structlog
from snowflake.connector.errors import ProgrammingError

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.session.SnowflakeSession import SnowflakeSession
from schemachange.session.Script import VersionedScript


@pytest.fixture
def session() -> SnowflakeSession:
    change_history_table = ChangeHistoryTable()
    logger = structlog.testing.CapturingLogger()

    with mock.patch("snowflake.connector.connect"):
        with mock.patch(
            "schemachange.session.SnowflakeSession.get_snowflake_identifier_string"
        ):
            # noinspection PyTypeChecker
            return SnowflakeSession(
                user="user",
                account="account",
                role="role",
                warehouse="warehouse",
                schemachange_version="3.6.1.dev",
                application="schemachange",
                change_history_table=change_history_table,
                logger=logger,
            )


class TestSnowflakeSession:
    def test_fetch_change_history_metadata_exists(self, session: SnowflakeSession):
        session.con.execute_string.return_value = [[["created", "last_altered"]]]
        result = session.fetch_change_history_metadata()
        assert result == {"created": "created", "last_altered": "last_altered"}
        assert session.con.execute_string.call_count == 1
        assert session.logger.calls[1][1][0] == "Executing query"

    def test_fetch_change_history_metadata_does_not_exist(
        self, session: SnowflakeSession
    ):
        session.con.execute_string.return_value = [[]]
        result = session.fetch_change_history_metadata()
        assert result == {}
        assert session.con.execute_string.call_count == 1
        assert session.logger.calls[1][1][0] == "Executing query"

    def test_apply_change_script_failure_records_history(
        self, session: SnowflakeSession
    ):
        script = VersionedScript.from_path(Path("V1__test.sql"))
        session.execute_snowflake_query = mock.Mock(
            side_effect=[Exception("boom"), None]
        )
        with (
            mock.patch.object(session, "reset_session"),
            mock.patch.object(session, "reset_query_tag"),
            pytest.raises(Exception),
        ):
            session.apply_change_script(script, "select 1", False, session.logger)
        assert session.execute_snowflake_query.call_count == 2
        insert_query = session.execute_snowflake_query.call_args_list[1].args[0]
        assert "Failed" in insert_query
        assert "ERROR_MESSAGE" in insert_query
        assert "boom" in insert_query

    def test_apply_change_script_missing_error_message_column(
        self, session: SnowflakeSession
    ):
        script = VersionedScript.from_path(Path("V1__test.sql"))
        session.execute_snowflake_query = mock.Mock(
            side_effect=[
                Exception("boom"),
                ProgrammingError("invalid identifier 'ERROR_MESSAGE'", 0, 0),
                None,
                None,
            ]
        )
        with (
            mock.patch.object(session, "reset_session"),
            mock.patch.object(session, "reset_query_tag"),
            pytest.raises(Exception),
        ):
            session.apply_change_script(script, "select 1", False, session.logger)
        assert session.execute_snowflake_query.call_count == 4
        first_insert = session.execute_snowflake_query.call_args_list[1].args[0]
        alter_stmt = session.execute_snowflake_query.call_args_list[2].args[0]
        retry_insert = session.execute_snowflake_query.call_args_list[3].args[0]
        assert "ERROR_MESSAGE" in first_insert
        assert "ALTER TABLE" in alter_stmt
        assert "ADD COLUMN" in alter_stmt
        assert "ERROR_MESSAGE" in alter_stmt
        assert "ERROR_MESSAGE" in retry_insert
