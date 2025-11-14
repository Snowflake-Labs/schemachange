from __future__ import annotations

from unittest import mock

import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.session.SnowflakeSession import SnowflakeSession


def test_session_parameters_merged_with_schemachange_query_tag():
    """Test that already-merged session parameters are passed to connect with schemachange QUERY_TAG appended"""
    change_history_table = ChangeHistoryTable()
    logger = structlog.testing.CapturingLogger()

    with mock.patch("snowflake.connector.connect") as mock_connect:
        mock_con = mock.MagicMock()
        mock_connect.return_value = mock_con

        # Session parameters already merged in get_merged_config (CLI > ENV > YAML > connections.toml)
        # This includes QUERY_TAG from connections.toml + CLI/ENV/YAML (already appended)
        merged_session_params = {
            "QUERY_TAG": "toml_tag;cli_tag",  # Already merged from all sources
            "QUOTED_IDENTIFIERS_IGNORE_CASE": "TRUE",  # CLI overrode toml
            "BINARY_OUTPUT_FORMAT": "HEX",  # From CLI
            "TIMESTAMP_OUTPUT_FORMAT": "YYYY-MM-DD",  # From toml
        }

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
                query_tag="custom_tag",
                session_parameters=merged_session_params,
            )

            # Verify connect was called once
            assert mock_connect.call_count == 1

            # Verify session_parameters were passed to connect with schemachange QUERY_TAG appended
            connect_kwargs = mock_connect.call_args.kwargs
            expected_params = {
                "QUERY_TAG": "toml_tag;cli_tag;schemachange 3.6.1.dev;custom_tag",
                "QUOTED_IDENTIFIERS_IGNORE_CASE": "TRUE",
                "BINARY_OUTPUT_FORMAT": "HEX",
                "TIMESTAMP_OUTPUT_FORMAT": "YYYY-MM-DD",
            }
            assert connect_kwargs["session_parameters"] == expected_params

            # Verify final parameters stored in session object
            assert session.session_parameters == expected_params


def test_session_parameters_with_connections_toml():
    """Test that session parameters work correctly when using connections.toml"""
    change_history_table = ChangeHistoryTable()
    logger = structlog.testing.CapturingLogger()

    with mock.patch("snowflake.connector.connect") as mock_connect:
        mock_con = mock.MagicMock()
        mock_connect.return_value = mock_con

        # Session parameters already merged in get_merged_config
        # connections.toml params + CLI/ENV/YAML overrides
        merged_session_params = {
            "QUERY_TAG": "toml_app_tag;deployment_tag",  # Appended from toml + CLI/ENV/YAML
            "QUOTED_IDENTIFIERS_IGNORE_CASE": "FALSE",  # From toml
        }

        with mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string"):
            session = SnowflakeSession(
                user="user",
                account="account",
                schemachange_version="3.6.1.dev",
                application="schemachange",
                change_history_table=change_history_table,
                logger=logger,
                connections_file_path="connections.toml",
                connection_name="test_connection",
                session_parameters=merged_session_params,
            )

            # Verify session_parameters were passed to connect with schemachange QUERY_TAG appended
            connect_kwargs = mock_connect.call_args.kwargs
            expected_params = {
                "QUERY_TAG": "toml_app_tag;deployment_tag;schemachange 3.6.1.dev",
                "QUOTED_IDENTIFIERS_IGNORE_CASE": "FALSE",
            }
            assert connect_kwargs["session_parameters"] == expected_params
            assert session.session_parameters == expected_params


def test_session_parameters_without_query_tag():
    """Test that schemachange QUERY_TAG is set when no QUERY_TAG in session_parameters"""
    change_history_table = ChangeHistoryTable()
    logger = structlog.testing.CapturingLogger()

    with mock.patch("snowflake.connector.connect") as mock_connect:
        mock_con = mock.MagicMock()
        mock_connect.return_value = mock_con

        merged_session_params = {
            "QUOTED_IDENTIFIERS_IGNORE_CASE": "FALSE",
        }

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
                query_tag="custom_tag",
                session_parameters=merged_session_params,
            )

            # Verify QUERY_TAG is created with just schemachange + custom_tag
            connect_kwargs = mock_connect.call_args.kwargs
            expected_params = {
                "QUERY_TAG": "schemachange 3.6.1.dev;custom_tag",
                "QUOTED_IDENTIFIERS_IGNORE_CASE": "FALSE",
            }
            assert connect_kwargs["session_parameters"] == expected_params
            assert session.session_parameters == expected_params


def test_session_parameters_empty():
    """Test behavior when no session parameters provided"""
    change_history_table = ChangeHistoryTable()
    logger = structlog.testing.CapturingLogger()

    with mock.patch("snowflake.connector.connect") as mock_connect:
        mock_con = mock.MagicMock()
        mock_connect.return_value = mock_con

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
                session_parameters=None,
            )

            # Verify only schemachange QUERY_TAG is set
            connect_kwargs = mock_connect.call_args.kwargs
            expected_params = {
                "QUERY_TAG": "schemachange 3.6.1.dev",
            }
            assert connect_kwargs["session_parameters"] == expected_params
            assert session.session_parameters == expected_params


def test_session_parameters_query_tag_only():
    """Test that query_tag parameter is incorporated into QUERY_TAG"""
    change_history_table = ChangeHistoryTable()
    logger = structlog.testing.CapturingLogger()

    with mock.patch("snowflake.connector.connect") as mock_connect:
        mock_con = mock.MagicMock()
        mock_connect.return_value = mock_con

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
                query_tag="production_deploy",
                session_parameters={},
            )

            # Verify QUERY_TAG includes both schemachange version and query_tag
            connect_kwargs = mock_connect.call_args.kwargs
            expected_params = {
                "QUERY_TAG": "schemachange 3.6.1.dev;production_deploy",
            }
            assert connect_kwargs["session_parameters"] == expected_params
            assert session.session_parameters == expected_params
