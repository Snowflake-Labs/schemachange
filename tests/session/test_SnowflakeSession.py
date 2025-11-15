from __future__ import annotations

from collections import defaultdict
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
        assert session.logger.calls[2][1][0] == "Executing query"

    def test_fetch_change_history_metadata_does_not_exist(self, session: SnowflakeSession):
        session.con.execute_string.return_value = [[]]
        result = session.fetch_change_history_metadata()
        assert result == {}
        assert session.con.execute_string.call_count == 1
        assert session.logger.calls[2][1][0] == "Executing query"

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

    def test_get_script_metadata_with_missing_change_history_table_dry_run(self, session: SnowflakeSession):
        """
        Test that get_script_metadata returns empty defaultdict when table doesn't exist during dry-run.

        This enables first-time deployments with --dry-run --create-change-history-table to preview
        changes without requiring the change history table to exist yet.
        """
        # Mock that table doesn't exist
        with mock.patch.object(session, "fetch_change_history_metadata", return_value=None):
            with mock.patch.object(session, "change_history_schema_exists", return_value=True):
                with mock.patch.object(session, "create_change_history_schema"):
                    with mock.patch.object(session, "create_change_history_table"):
                        versioned_scripts, r_scripts_checksum, max_published_version = session.get_script_metadata(
                            create_change_history_table=True, dry_run=True
                        )

        # Should return defaultdict(dict) for versioned_scripts to avoid AttributeError
        assert isinstance(versioned_scripts, defaultdict)
        assert versioned_scripts.default_factory == dict
        assert r_scripts_checksum is None
        assert max_published_version is None

    def test_get_script_metadata_defaultdict_get_returns_none(self, session: SnowflakeSession):
        """
        Test that defaultdict(dict).get(key) returns None for missing keys.

        This is critical because deploy.py uses versioned_scripts.get(script_name) and expects
        None for scripts that haven't been applied yet.
        """
        # Mock that table doesn't exist
        with mock.patch.object(session, "fetch_change_history_metadata", return_value=None):
            with mock.patch.object(session, "change_history_schema_exists", return_value=True):
                with mock.patch.object(session, "create_change_history_schema"):
                    with mock.patch.object(session, "create_change_history_table"):
                        versioned_scripts, _, _ = session.get_script_metadata(
                            create_change_history_table=True, dry_run=True
                        )

        # .get() should return None (standard dict behavior, doesn't trigger default factory)
        result = versioned_scripts.get("V1.0.0__test_script.sql")
        assert result is None

        # Verify __getitem__ would trigger factory (not used by deploy.py)
        result2 = versioned_scripts["V1.0.0__new_script.sql"]
        assert result2 == {}  # Default factory returns empty dict

    def test_get_script_metadata_error_when_table_missing_without_create_flag(self, session: SnowflakeSession):
        """
        Test that get_script_metadata raises clear error when table doesn't exist and create flag is False.
        """
        with mock.patch.object(session, "fetch_change_history_metadata", return_value=None):
            with pytest.raises(ValueError, match="Unable to find change history table"):
                session.get_script_metadata(create_change_history_table=False, dry_run=True)

    @pytest.mark.parametrize(
        "create_flag,dry_run_flag,table_exists,should_error",
        [
            (False, False, True, False),  # Normal deploy, table exists
            (False, False, False, True),  # Normal deploy, no table, no create → ERROR
            (False, True, True, False),  # Dry-run, table exists
            (False, True, False, True),  # Dry-run, no table, no create → ERROR
            (True, False, False, False),  # Normal deploy with create flag, no table → creates it
            (True, True, False, False),  # Dry-run with create flag, no table → works (issue #326)
        ],
    )
    def test_get_script_metadata_flag_combinations(
        self, session: SnowflakeSession, create_flag, dry_run_flag, table_exists, should_error
    ):
        """Test all combinations of create_change_history_table and dry_run flags."""
        metadata = {"last_altered": "2025-11-14"} if table_exists else None

        with mock.patch.object(session, "fetch_change_history_metadata", return_value=metadata):
            with mock.patch.object(session, "change_history_schema_exists", return_value=True):
                with mock.patch.object(session, "create_change_history_schema"):
                    with mock.patch.object(session, "create_change_history_table"):
                        with mock.patch.object(session, "fetch_versioned_scripts", return_value=({}, None)):
                            with mock.patch.object(session, "fetch_repeatable_scripts", return_value={}):
                                if should_error:
                                    with pytest.raises(ValueError):
                                        session.get_script_metadata(
                                            create_change_history_table=create_flag, dry_run=dry_run_flag
                                        )
                                else:
                                    versioned_scripts, _, _ = session.get_script_metadata(
                                        create_change_history_table=create_flag, dry_run=dry_run_flag
                                    )
                                    assert versioned_scripts is not None
