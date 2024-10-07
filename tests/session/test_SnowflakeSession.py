from __future__ import annotations

from unittest import mock

import pytest
import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.session.Credential import ExternalBrowserCredential
from schemachange.session.SnowflakeSession import SnowflakeSession


@pytest.fixture
def session() -> SnowflakeSession:
    credential = ExternalBrowserCredential(password="password")
    change_history_table = ChangeHistoryTable()
    logger = structlog.testing.CapturingLogger()

    with mock.patch("snowflake.connector.connect"):
        # noinspection PyTypeChecker
        return SnowflakeSession(
            snowflake_user="user",
            snowflake_account="account",
            snowflake_role="role",
            snowflake_warehouse="warehouse",
            schemachange_version="3.6.1.dev",
            application="schemachange",
            credential=credential,
            change_history_table=change_history_table,
            logger=logger,
        )


class TestSnowflakeSession:
    def test_fetch_change_history_metadata_exists(self, session: SnowflakeSession):
        session.con.execute_string.return_value = [[["created", "last_altered"]]]
        result = session.fetch_change_history_metadata()
        assert result == {"created": "created", "last_altered": "last_altered"}
        assert session.con.execute_string.call_count == 1
        assert session.logger.calls[0][1][0] == "Executing query"

    def test_fetch_change_history_metadata_does_not_exist(
        self, session: SnowflakeSession
    ):
        session.con.execute_string.return_value = [[]]
        result = session.fetch_change_history_metadata()
        assert result == {}
        assert session.con.execute_string.call_count == 1
        assert session.logger.calls[0][1][0] == "Executing query"
