from __future__ import annotations

from unittest import mock

import pytest
import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.session.SnowflakeSession import SnowflakeSession


@pytest.fixture
def mock_snowflake_connect():
    with mock.patch("snowflake.connector.connect") as mock_connect:
        mock_con = mock.MagicMock()
        mock_con._session_parameters = {
            "QUOTED_IDENTIFIERS_IGNORE_CASE": False,
            "QUERY_TAG": "existing_tag"
        }
        mock_connect.return_value = mock_con
        yield mock_connect


def test_session_parameters_from_toml(mock_snowflake_connect):
    """Test that session parameters from connections.toml are respected and merged with QUERY_TAG"""
    change_history_table = ChangeHistoryTable()
    logger = structlog.testing.CapturingLogger()

    with mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string"):
        session = SnowflakeSession(
            user="user",
            account="account",
            role="role",
            warehouse="warehouse", 
            schemachange_version="3.6.1.dev",
            application="schemachange",
            change_history_table=change_history_table,
            logger=logger,
            connections_file_path="connections.toml",
            connection_name="test_connection",
            query_tag="custom_tag"
        )

        first_call_kwargs = mock_snowflake_connect.call_args_list[0][1]
        assert first_call_kwargs["connections_file_path"] == "connections.toml"
        assert first_call_kwargs["connection_name"] == "test_connection"
        assert "session_parameters" not in first_call_kwargs

        second_call_kwargs = mock_snowflake_connect.call_args_list[1][1]
        assert second_call_kwargs["session_parameters"] == {
            "QUOTED_IDENTIFIERS_IGNORE_CASE": False,
            "QUERY_TAG": "existing_tag;schemachange 3.6.1.dev;custom_tag"
        }