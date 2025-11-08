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
        with mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string"):
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

    def test_fetch_change_history_metadata_does_not_exist(self, session: SnowflakeSession):
        session.con.execute_string.return_value = [[]]
        result = session.fetch_change_history_metadata()
        assert result == {}
        assert session.con.execute_string.call_count == 1
        assert session.logger.calls[1][1][0] == "Executing query"

    def test_snowflake_session_with_additional_params_from_yaml_v2(self):
        """Test that additional_snowflake_params from YAML v2 are passed to connector."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        additional_params = {
            "client-session-keep-alive": True,
            "login-timeout": 60,
            "network-timeout": 120,
        }

        with mock.patch("snowflake.connector.connect") as mock_connect:
            with mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string"):
                # noinspection PyTypeChecker
                SnowflakeSession(
                    user="user",
                    account="account",
                    role="role",
                    warehouse="warehouse",
                    schemachange_version="3.6.1.dev",
                    application="schemachange",
                    change_history_table=change_history_table,
                    logger=logger,
                    additional_snowflake_params=additional_params,
                )

                # Verify snowflake.connector.connect was called with additional params
                call_kwargs = mock_connect.call_args.kwargs
                assert call_kwargs["client_session_keep_alive"] is True
                assert call_kwargs["login_timeout"] == 60
                assert call_kwargs["network_timeout"] == 120

    def test_snowflake_session_with_additional_params_from_env(self):
        """Test that additional_snowflake_params from env vars are passed to connector."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        additional_params = {
            "client_session_keep_alive": True,
            "login_timeout": 60,
        }

        with mock.patch("snowflake.connector.connect") as mock_connect:
            with mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string"):
                # noinspection PyTypeChecker
                SnowflakeSession(
                    user="user",
                    account="account",
                    role="role",
                    warehouse="warehouse",
                    schemachange_version="3.6.1.dev",
                    application="schemachange",
                    change_history_table=change_history_table,
                    logger=logger,
                    additional_snowflake_params=additional_params,
                )

                # Verify snowflake.connector.connect was called with additional params
                call_kwargs = mock_connect.call_args.kwargs
                assert call_kwargs["client_session_keep_alive"] is True
                assert call_kwargs["login_timeout"] == 60

    def test_snowflake_session_explicit_params_override_additional_params(self):
        """Test that explicit params override additional_snowflake_params."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        # additional_params has account, but explicit param should win
        additional_params = {
            "account": "additional_account",
            "client_session_keep_alive": True,
        }

        with mock.patch("snowflake.connector.connect") as mock_connect:
            with mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string"):
                # noinspection PyTypeChecker
                SnowflakeSession(
                    user="explicit_user",
                    account="explicit_account",  # Explicit param should override
                    role="explicit_role",
                    warehouse="warehouse",
                    schemachange_version="3.6.1.dev",
                    application="schemachange",
                    change_history_table=change_history_table,
                    logger=logger,
                    additional_snowflake_params=additional_params,
                )

                # Verify explicit params win
                call_kwargs = mock_connect.call_args.kwargs
                assert call_kwargs["account"] == "explicit_account"
                assert call_kwargs["user"] == "explicit_user"
                assert call_kwargs["role"] == "explicit_role"
                # But additional param still passes through
                assert call_kwargs["client_session_keep_alive"] is True

    def test_snowflake_session_no_additional_params(self):
        """Test that SnowflakeSession works without additional_snowflake_params."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            with mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string"):
                # noinspection PyTypeChecker
                SnowflakeSession(
                    user="user",
                    account="account",
                    role="role",
                    warehouse="warehouse",
                    schemachange_version="3.6.1.dev",
                    application="schemachange",
                    change_history_table=change_history_table,
                    logger=logger,
                    additional_snowflake_params=None,  # Explicit None
                )

                # Verify connector was called with basic params
                call_kwargs = mock_connect.call_args.kwargs
                assert call_kwargs["account"] == "account"
                assert call_kwargs["user"] == "user"
                # No additional params should be present
                assert "client_session_keep_alive" not in call_kwargs
                assert "login_timeout" not in call_kwargs
