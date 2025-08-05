from __future__ import annotations

from unittest import mock
from pathlib import Path

import pytest
import structlog

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

    def test_apply_change_script_failure_does_not_record_history(
        self, session: SnowflakeSession
    ):
        script = VersionedScript.from_path(Path("V1__test.sql"))
        session.execute_snowflake_query = mock.Mock(side_effect=[Exception("boom")])
        with (
            mock.patch.object(session, "reset_session"),
            mock.patch.object(session, "reset_query_tag"),
            pytest.raises(Exception),
        ):
            session.apply_change_script(script, "select 1", False, session.logger)
        # Only the script execution should be attempted
        assert session.execute_snowflake_query.call_count == 1
