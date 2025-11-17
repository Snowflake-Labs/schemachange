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

    with mock.patch("snowflake.connector.connect") as mock_connect:
        # Mock the connection object
        mock_conn = mock.Mock()
        mock_conn.account = "account"
        mock_conn.user = "user"
        mock_conn.role = "role"
        mock_conn.warehouse = "warehouse"
        mock_conn.database = None
        mock_conn.schema = None
        mock_conn.session_id = "session_123"
        mock_connect.return_value = mock_conn

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
        # Reset call count after initialization (which calls execute_string for USE commands)
        session.con.execute_string.reset_mock()

        session.con.execute_string.return_value = [[["created", "last_altered"]]]
        result = session.fetch_change_history_metadata()
        assert result == {"created": "created", "last_altered": "last_altered"}
        assert session.con.execute_string.call_count == 1

    def test_fetch_change_history_metadata_does_not_exist(self, session: SnowflakeSession):
        # Reset call count after initialization (which calls execute_string for USE commands)
        session.con.execute_string.reset_mock()

        session.con.execute_string.return_value = [[]]
        result = session.fetch_change_history_metadata()
        assert result == {}
        assert session.con.execute_string.call_count == 1

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

        This enables first-time deployments with --dry-run --create-change-history-table --initial-deployment
        to preview changes without requiring the change history table to exist yet.
        """
        # Mock that table doesn't exist (returns empty dict)
        with mock.patch.object(session, "fetch_change_history_metadata", return_value={}):
            with mock.patch.object(session, "change_history_schema_exists", return_value=True):
                with mock.patch.object(session, "create_change_history_schema"):
                    with mock.patch.object(session, "create_change_history_table"):
                        versioned_scripts, r_scripts_checksum, max_published_version = session.get_script_metadata(
                            create_change_history_table=True, initial_deployment=True, dry_run=True
                        )

        # Should return defaultdict(dict) for versioned_scripts to avoid AttributeError
        assert isinstance(versioned_scripts, defaultdict)
        assert versioned_scripts.default_factory is dict
        assert r_scripts_checksum is None
        assert max_published_version is None

    def test_get_script_metadata_defaultdict_get_returns_none(self, session: SnowflakeSession):
        """
        Test that defaultdict(dict).get(key) returns None for missing keys.

        This is critical because deploy.py uses versioned_scripts.get(script_name) and expects
        None for scripts that haven't been applied yet during initial deployment.
        """
        # Mock that table doesn't exist (initial deployment scenario, returns empty dict)
        with mock.patch.object(session, "fetch_change_history_metadata", return_value={}):
            with mock.patch.object(session, "change_history_schema_exists", return_value=True):
                with mock.patch.object(session, "create_change_history_schema"):
                    with mock.patch.object(session, "create_change_history_table"):
                        versioned_scripts, _, _ = session.get_script_metadata(
                            create_change_history_table=True, initial_deployment=True, dry_run=True
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

        Regression test for bug: fetch_change_history_metadata returns {} (empty dict), not None.
        """
        with mock.patch.object(session, "fetch_change_history_metadata", return_value={}):
            with pytest.raises(ValueError, match="Unable to find change history table"):
                session.get_script_metadata(create_change_history_table=False, initial_deployment=False, dry_run=True)

    @pytest.mark.parametrize(
        "create_flag,initial_flag,dry_run_flag,table_exists,should_error,error_match",
        [
            # Normal operations (no initial_deployment flag)
            (False, False, False, True, False, None),  # Normal deploy, table exists
            (
                False,
                False,
                False,
                False,
                True,
                "Unable to find change history table",
            ),  # Normal deploy, no table, no create → ERROR
            (False, False, True, True, False, None),  # Dry-run, table exists
            (
                False,
                False,
                True,
                False,
                True,
                "Unable to find change history table",
            ),  # Dry-run, no table, no create → ERROR
            (True, False, False, True, False, None),  # Normal deploy with create flag, table exists
            (
                True,
                False,
                False,
                False,
                True,
                "Change history table .* does not exist",
            ),  # Table missing, create=true but initial=false → ERROR (new behavior)
            (True, False, True, True, False, None),  # Dry-run with create flag, table exists
            (
                True,
                False,
                True,
                False,
                True,
                "Change history table .* does not exist",
            ),  # Dry-run, create=true but initial=false, no table → ERROR (new behavior)
            # Initial deployment scenarios
            (True, True, False, False, False, None),  # Initial deploy: create table and apply all
            (True, True, True, False, False, None),  # Initial deploy dry-run: preview table creation and scripts
            (True, True, False, True, True, "already exists"),  # Initial deploy but table exists → ERROR
            (True, True, True, True, True, "already exists"),  # Initial deploy dry-run but table exists → ERROR
            (
                False,
                True,
                False,
                False,
                True,
                "requires.*create-change-history-table",
            ),  # Initial deploy without create flag → ERROR
            (
                False,
                True,
                True,
                False,
                True,
                "requires.*create-change-history-table",
            ),  # Initial deploy dry-run without create flag → ERROR
        ],
    )
    def test_get_script_metadata_flag_combinations(
        self,
        session: SnowflakeSession,
        create_flag,
        initial_flag,
        dry_run_flag,
        table_exists,
        should_error,
        error_match,
    ):
        """Test all combinations of create_change_history_table, initial_deployment, and dry_run flags."""
        metadata = {"last_altered": "2025-11-14"} if table_exists else {}

        with mock.patch.object(session, "fetch_change_history_metadata", return_value=metadata):
            with mock.patch.object(session, "change_history_schema_exists", return_value=True):
                with mock.patch.object(session, "create_change_history_schema"):
                    with mock.patch.object(session, "create_change_history_table"):
                        with mock.patch.object(session, "fetch_versioned_scripts", return_value=({}, None)):
                            with mock.patch.object(session, "fetch_repeatable_scripts", return_value={}):
                                if should_error:
                                    with pytest.raises(ValueError, match=error_match):
                                        session.get_script_metadata(
                                            create_change_history_table=create_flag,
                                            initial_deployment=initial_flag,
                                            dry_run=dry_run_flag,
                                        )
                                else:
                                    versioned_scripts, _, _ = session.get_script_metadata(
                                        create_change_history_table=create_flag,
                                        initial_deployment=initial_flag,
                                        dry_run=dry_run_flag,
                                    )
                                    assert versioned_scripts is not None

    def test_initial_deployment_creates_table_and_returns_empty_metadata(self, session: SnowflakeSession):
        """Test that initial_deployment=True creates table and returns empty metadata."""
        with mock.patch.object(session, "fetch_change_history_metadata", return_value={}):
            with mock.patch.object(session, "change_history_schema_exists", return_value=True):
                with mock.patch.object(session, "create_change_history_schema"):
                    with mock.patch.object(session, "create_change_history_table") as mock_create_table:
                        versioned_scripts, r_scripts, max_version = session.get_script_metadata(
                            create_change_history_table=True,
                            initial_deployment=True,
                            dry_run=False,
                        )

                        # Should create the table
                        mock_create_table.assert_called_once_with(dry_run=False)
                        # Should return empty metadata (all scripts are new)
                        assert len(versioned_scripts) == 0
                        assert r_scripts is None
                        assert max_version is None

    def test_initial_deployment_dry_run_logs_correctly(self, session: SnowflakeSession):
        """Test that initial_deployment=True with dry_run logs appropriate messages."""
        with mock.patch.object(session, "fetch_change_history_metadata", return_value={}):
            with mock.patch.object(session, "change_history_schema_exists", return_value=True):
                with mock.patch.object(session, "create_change_history_schema"):
                    with mock.patch.object(session, "create_change_history_table") as mock_create_table:
                        versioned_scripts, _, _ = session.get_script_metadata(
                            create_change_history_table=True,
                            initial_deployment=True,
                            dry_run=True,
                        )

                        # Should still call create_change_history_table (it will log but not execute)
                        mock_create_table.assert_called_once_with(dry_run=True)
                        # Should return empty metadata
                        assert len(versioned_scripts) == 0

    def test_error_when_table_missing_without_initial_deployment_flag(self, session: SnowflakeSession):
        """Test that missing table with create=true but initial=false raises error with helpful message."""
        with mock.patch.object(session, "fetch_change_history_metadata", return_value={}):
            with pytest.raises(ValueError, match="If this is the initial deployment.*add --initial-deployment"):
                session.get_script_metadata(
                    create_change_history_table=True,
                    initial_deployment=False,
                    dry_run=False,
                )

    def test_initialize_session_context_all_parameters(self):
        """Test session initialization with all context parameters (role, warehouse, database, schema)."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            mock_conn = mock.Mock()
            mock_conn.account = "test_account"
            mock_conn.user = "test_user"
            mock_conn.role = "TEST_ROLE"
            mock_conn.warehouse = "TEST_WH"
            mock_conn.database = "TEST_DB"
            mock_conn.schema = "TEST_SCHEMA"
            mock_conn.session_id = "session_123"
            mock_connect.return_value = mock_conn

            session = SnowflakeSession(
                user="test_user",
                account="test_account",
                role="TEST_ROLE",
                warehouse="TEST_WH",
                database="TEST_DB",
                schema="TEST_SCHEMA",
                schemachange_version="4.2.0",
                application="schemachange",
                change_history_table=change_history_table,
                logger=logger,
            )

            # Verify session object was created successfully
            assert session is not None
            assert session.warehouse == "TEST_WH"
            assert session.role == "TEST_ROLE"

            # Verify execute_string was called for session initialization
            assert mock_conn.execute_string.call_count == 1

            # Verify all USE commands were executed
            executed_query = mock_conn.execute_string.call_args[0][0]
            assert "USE ROLE IDENTIFIER('TEST_ROLE');" in executed_query
            assert "USE WAREHOUSE IDENTIFIER('TEST_WH');" in executed_query
            assert "USE DATABASE IDENTIFIER('TEST_DB');" in executed_query
            assert "USE SCHEMA IDENTIFIER('TEST_SCHEMA');" in executed_query

    def test_initialize_session_context_warehouse_only(self):
        """Test session initialization with only warehouse parameter (issue #233, #235)."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            mock_conn = mock.Mock()
            mock_conn.account = "test_account"
            mock_conn.user = "test_user"
            mock_conn.role = None
            mock_conn.warehouse = "DEPLOY_WH"
            mock_conn.database = None
            mock_conn.schema = None
            mock_conn.session_id = "session_123"
            mock_connect.return_value = mock_conn

            session = SnowflakeSession(
                user="test_user",
                account="test_account",
                warehouse="DEPLOY_WH",
                schemachange_version="4.2.0",
                application="schemachange",
                change_history_table=change_history_table,
                logger=logger,
            )

            # Verify session object was created successfully
            assert session is not None
            assert session.warehouse == "DEPLOY_WH"
            assert session.role is None

            # Verify execute_string was called for warehouse initialization
            assert mock_conn.execute_string.call_count == 1

            # Verify only USE WAREHOUSE was executed
            executed_query = mock_conn.execute_string.call_args[0][0]
            assert "USE WAREHOUSE IDENTIFIER('DEPLOY_WH');" in executed_query
            assert "USE ROLE" not in executed_query
            assert "USE DATABASE" not in executed_query
            assert "USE SCHEMA" not in executed_query

    def test_initialize_session_context_no_parameters(self):
        """Test session initialization with no context parameters doesn't execute USE commands."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            mock_conn = mock.Mock()
            mock_conn.account = "test_account"
            mock_conn.user = "test_user"
            mock_conn.role = None
            mock_conn.warehouse = None
            mock_conn.database = None
            mock_conn.schema = None
            mock_conn.session_id = "session_123"
            mock_connect.return_value = mock_conn

            session = SnowflakeSession(
                user="test_user",
                account="test_account",
                schemachange_version="4.2.0",
                application="schemachange",
                change_history_table=change_history_table,
                logger=logger,
            )

            # Verify session object was created successfully
            assert session is not None

            # Verify execute_string was NOT called (no USE commands needed)
            assert mock_conn.execute_string.call_count == 0

    def test_initialize_session_context_handles_errors(self):
        """Test session initialization handles errors gracefully with helpful message."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            mock_conn = mock.Mock()
            mock_conn.account = "test_account"
            mock_conn.user = "test_user"
            mock_conn.role = "INVALID_ROLE"
            mock_conn.warehouse = "TEST_WH"
            mock_conn.database = "TEST_DB"
            mock_conn.schema = "TEST_SCHEMA"
            mock_conn.session_id = "session_123"

            # Simulate error when executing USE commands
            mock_conn.execute_string.side_effect = Exception("Insufficient privileges")
            mock_connect.return_value = mock_conn

            with pytest.raises(ValueError, match="Failed to initialize Snowflake session context"):
                _ = SnowflakeSession(
                    user="test_user",
                    account="test_account",
                    role="INVALID_ROLE",
                    warehouse="TEST_WH",
                    database="TEST_DB",
                    schema="TEST_SCHEMA",
                    schemachange_version="4.2.0",
                    application="schemachange",
                    change_history_table=change_history_table,
                    logger=logger,
                )

    def test_missing_warehouse_connects_but_queries_will_fail(self):
        """Test that connection succeeds without warehouse, but operations requiring warehouse will fail."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            mock_conn = mock.Mock()
            mock_conn.account = "test_account"
            mock_conn.user = "test_user"
            mock_conn.role = "TEST_ROLE"
            mock_conn.warehouse = None  # No warehouse specified
            mock_conn.database = "TEST_DB"
            mock_conn.schema = "TEST_SCHEMA"
            mock_conn.session_id = "session_123"
            mock_connect.return_value = mock_conn

            # Connection should succeed
            session = SnowflakeSession(
                user="test_user",
                account="test_account",
                role="TEST_ROLE",
                warehouse=None,  # No warehouse
                database="TEST_DB",
                schema="TEST_SCHEMA",
                schemachange_version="4.2.0",
                application="schemachange",
                change_history_table=change_history_table,
                logger=logger,
            )

            # Verify execute_string was called (for role, database, schema - but not warehouse)
            assert mock_conn.execute_string.call_count == 1
            executed_query = mock_conn.execute_string.call_args[0][0]
            assert "USE ROLE IDENTIFIER('TEST_ROLE');" in executed_query
            assert "USE DATABASE IDENTIFIER('TEST_DB');" in executed_query
            assert "USE SCHEMA IDENTIFIER('TEST_SCHEMA');" in executed_query
            assert "USE WAREHOUSE" not in executed_query  # Warehouse should NOT be in query

            # Now simulate a query that requires warehouse (like fetching change history)
            mock_conn.execute_string.reset_mock()
            mock_conn.execute_string.side_effect = Exception(
                "000606 (57P03): No active warehouse selected in the current session. "
                "Select an active warehouse with the 'use warehouse' command."
            )

            # This would fail with warehouse error
            with pytest.raises(Exception, match="No active warehouse selected"):
                session.fetch_change_history_metadata()

    def test_missing_all_context_parameters_allows_connection(self):
        """Test that connection can be established without any context parameters."""
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            mock_conn = mock.Mock()
            mock_conn.account = "test_account"
            mock_conn.user = "test_user"
            mock_conn.role = None
            mock_conn.warehouse = None
            mock_conn.database = None
            mock_conn.schema = None
            mock_conn.session_id = "session_123"
            mock_connect.return_value = mock_conn

            # Connection should succeed
            session = SnowflakeSession(
                user="test_user",
                account="test_account",
                schemachange_version="4.2.0",
                application="schemachange",
                change_history_table=change_history_table,
                logger=logger,
            )

            # Verify session object was created successfully
            assert session is not None

            # No USE commands should be executed
            assert mock_conn.execute_string.call_count == 0

            # Session object should have None for context parameters
            assert session.role is None
            assert session.warehouse is None
            assert session.database is None
            assert session.schema is None

    def test_warehouse_required_for_schemachange_operations(self):
        """
        Document that warehouse is effectively required for schemachange operations.

        While Snowflake allows connection without a warehouse, schemachange needs one for:
        - Querying INFORMATION_SCHEMA.TABLES (change history lookup)
        - Creating change history table
        - Executing SQL scripts

        This test documents the expected behavior and error message users will see.
        """
        change_history_table = ChangeHistoryTable()
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            mock_conn = mock.Mock()
            mock_conn.account = "test_account"
            mock_conn.user = "test_user"
            mock_conn.role = None
            mock_conn.warehouse = None  # No warehouse
            mock_conn.database = None
            mock_conn.schema = None
            mock_conn.session_id = "session_123"

            # First call: successful connection (no USE commands)
            # Subsequent calls: warehouse error when querying
            mock_conn.execute_string.side_effect = [
                Exception(
                    "000606 (57P03): No active warehouse selected in the current session. "
                    "Select an active warehouse with the 'use warehouse' command."
                )
            ]
            mock_connect.return_value = mock_conn

            session = SnowflakeSession(
                user="test_user",
                account="test_account",
                schemachange_version="4.2.0",
                application="schemachange",
                change_history_table=change_history_table,
                logger=logger,
            )

            # Attempting any schemachange operation will fail
            with pytest.raises(Exception, match="No active warehouse selected"):
                session.fetch_change_history_metadata()
