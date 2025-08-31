from __future__ import annotations

from unittest import mock

import pytest
import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.session.SnowflakeSession import SnowflakeSession


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
        # Mock the HistorySession creation
        mock_history_session = mock.MagicMock()
        mock_history_session.fetch_change_history_metadata.return_value = {
            "created": "created",
            "last_altered": "last_altered",
        }

        with mock.patch(
            "schemachange.session.HistorySession.HistorySession",
            return_value=mock_history_session,
        ):
            result = session.fetch_change_history_metadata()
            assert result == {"created": "created", "last_altered": "last_altered"}
            mock_history_session.fetch_change_history_metadata.assert_called_once()

    def test_fetch_change_history_metadata_does_not_exist(
        self, session: SnowflakeSession
    ):
        # Mock the HistorySession creation
        mock_history_session = mock.MagicMock()
        mock_history_session.fetch_change_history_metadata.return_value = {}

        with mock.patch(
            "schemachange.session.HistorySession.HistorySession",
            return_value=mock_history_session,
        ):
            result = session.fetch_change_history_metadata()
            assert result == {}
            mock_history_session.fetch_change_history_metadata.assert_called_once()
