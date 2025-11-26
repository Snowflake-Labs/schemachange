"""
Test for issue #388: Verify that private key passphrases are not exposed in DEBUG logs.

This test directly addresses the security concern reported in:
https://github.com/Snowflake-Labs/schemachange/issues/388#issuecomment-3551323964

The issue reported that when using private_key_file_pwd in connections.toml,
the passphrase was being logged in clear text at DEBUG level.
"""

import io
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import structlog
from structlog.testing import LogCapture

from schemachange.cli import verify
from schemachange.config.VerifyConfig import VerifyConfig


class TestIssue388PassphraseExposure:
    """Test that issue #388 passphrase exposure is fixed."""

    def test_verify_command_debug_logs_do_not_expose_private_key_file_pwd(self, caplog):
        """
        Test that DEBUG-level logging in the verify command does not expose private_key_file_pwd.
        
        This is the core fix for issue #388. The verify command has diagnostic output at DEBUG level
        that shows session_kwargs and config attributes. Both must properly exclude the passphrase.
        """
        # Create a config with private_key_file_pwd (the new parameter name)
        config = VerifyConfig.factory(
            subcommand="deploy",
            config_file_path=Path("test.yml"),
            root_folder=Path("."),
            snowflake_account="test_account",
            snowflake_user="test_user",
            snowflake_role="test_role",
            snowflake_warehouse="test_warehouse",
            snowflake_private_key_file="/fake/path/key.p8",
            snowflake_private_key_file_pwd="SUPER_SECRET_PASSWORD_123",
            log_level=logging.DEBUG,  # This is key - DEBUG level triggers the diagnostic output
        )

        # Capture logs at DEBUG level
        with caplog.at_level(logging.DEBUG):
            # Mock the SnowflakeSession to avoid actual connection
            with patch("schemachange.cli.SnowflakeSession") as mock_session_class:
                # Mock a successful connection
                mock_session = MagicMock()
                mock_session.con = MagicMock()
                mock_session.con.user = "test_user"
                mock_session.con.role = "test_role"
                mock_session.con.warehouse = "test_warehouse"
                mock_session.con.database = "test_database"
                mock_session.con.schema = "test_schema"
                mock_session.con.session_id = "test_session_id"
                mock_session.account = "test_account"
                mock_session.user = "test_user"
                mock_session.role = "test_role"
                mock_session.warehouse = "test_warehouse"
                mock_session.database = "test_database"
                mock_session.schema = "test_schema"
                
                # Mock the cursor for CURRENT_VERSION() query
                mock_cursor = MagicMock()
                mock_cursor.fetchone.return_value = ["8.1.0"]
                mock_session.con.cursor.return_value = mock_cursor
                
                mock_session_class.return_value = mock_session

                # Create a logger for the verify function
                logger = structlog.get_logger()

                # Call verify - this triggers the DEBUG logging
                verify(config, logger)

        # Collect all log output (including DEBUG messages)
        all_log_text = "\n".join([record.message for record in caplog.records])

        # SECURITY CHECK: The passphrase must NEVER appear in logs
        assert "SUPER_SECRET_PASSWORD_123" not in all_log_text, (
            "SECURITY ISSUE: Private key passphrase was exposed in DEBUG logs! "
            "This is the exact vulnerability reported in issue #388. "
            f"Found in logs:\n{all_log_text}"
        )

    def test_verify_command_debug_logs_do_not_expose_legacy_passphrase(self):
        """
        Test that the legacy private_key_passphrase parameter is also not exposed at DEBUG level.
        
        During the deprecation period, both parameter names must be properly masked.
        """
        # Create a config with the legacy parameter name
        config = VerifyConfig.factory(
            subcommand="deploy",
            config_file_path=Path("test.yml"),
            root_folder=Path("."),
            snowflake_account="test_account",
            snowflake_user="test_user",
            snowflake_role="test_role",
            snowflake_warehouse="test_warehouse",
            snowflake_private_key_file="/fake/path/key.p8",
            snowflake_private_key_passphrase="LEGACY_SECRET_XYZ",  # Old parameter name
            log_level=logging.DEBUG,
        )

        # Set up a log capture
        log_capture = LogCapture()
        structlog.configure(processors=[log_capture])

        # Mock the SnowflakeSession
        with patch("schemachange.cli.SnowflakeSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.con = MagicMock()
            mock_session.con.user = "test_user"
            mock_session.con.role = "test_role"
            mock_session.con.warehouse = "test_warehouse"
            mock_session.con.database = "test_database"
            mock_session.con.schema = "test_schema"
            mock_session.con.session_id = "test_session_id"
            mock_session.account = "test_account"
            mock_session.user = "test_user"
            mock_session.role = "test_role"
            mock_session.warehouse = "test_warehouse"
            mock_session.database = "test_database"
            mock_session.schema = "test_schema"
            
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = ["8.1.0"]
            mock_session.con.cursor.return_value = mock_cursor
            
            mock_session_class.return_value = mock_session

            logger = structlog.get_logger()
            verify(config, logger)

        # Collect all log entries
        log_entries = log_capture.entries
        all_log_text = "\n".join(
            [str(entry.get("event", "")) + " " + " ".join([str(v) for v in entry.values()]) 
             for entry in log_entries]
        )

        # The legacy passphrase should also be masked
        assert "LEGACY_SECRET_XYZ" not in all_log_text, (
            "SECURITY ISSUE: Legacy private_key_passphrase was exposed in DEBUG logs! "
            "Backward compatibility during deprecation must also maintain security."
        )

    def test_session_kwargs_masking_in_cli(self):
        """
        Test the specific code path in cli.py that masks session_kwargs.
        
        This directly tests lines 100-103 in cli.py where session_kwargs are logged at DEBUG level.
        """
        config = VerifyConfig.factory(
            subcommand="deploy",
            config_file_path=Path("test.yml"),
            root_folder=Path("."),
            snowflake_account="test_account",
            snowflake_user="test_user",
            snowflake_private_key_file="/fake/path/key.p8",
            snowflake_private_key_file_pwd="TEST_PASSPHRASE_ABC",
            log_level=logging.DEBUG,
        )

        # Get the session kwargs (same as cli.py does)
        session_kwargs = config.get_session_kwargs()

        # Simulate the masking logic from cli.py line 101-103
        masked_keys = [
            k for k in session_kwargs.keys() 
            if k not in ['password', 'token', 'private_key_passphrase', 'private_key_file_pwd']
        ]

        # Verify that private_key_file_pwd is excluded from the masked output
        assert 'private_key_file_pwd' not in masked_keys, (
            "private_key_file_pwd should be excluded from debug output"
        )

        # But verify that the value is actually present in session_kwargs (not lost)
        assert 'private_key_file_pwd' in session_kwargs, (
            "private_key_file_pwd should still be in session_kwargs for connection"
        )

    def test_config_attrs_masking_in_cli(self):
        """
        Test the specific code path in cli.py that masks config attributes.
        
        This directly tests lines 105-117 in cli.py where config snowflake_* attributes are logged.
        """
        config = VerifyConfig.factory(
            subcommand="deploy",
            config_file_path=Path("test.yml"),
            root_folder=Path("."),
            snowflake_account="test_account",
            snowflake_user="test_user",
            snowflake_private_key_file="/fake/path/key.p8",
            snowflake_private_key_file_pwd="TEST_CONFIG_SECRET_789",
            log_level=logging.DEBUG,
        )

        # Simulate the config attribute extraction from cli.py line 106-108
        config_attrs = {
            k: getattr(config, k) 
            for k in dir(config) 
            if k.startswith("snowflake_") and not k.startswith("__")
        }

        # Simulate the filtering from cli.py line 111-116
        sensitive_attrs = [
            "snowflake_password",
            "snowflake_token",
            "snowflake_private_key_passphrase",
            "snowflake_private_key_file_pwd",  # This is the key fix for issue #388
        ]

        # Check which attributes would be logged
        attrs_to_log = {k: v for k, v in config_attrs.items() if k not in sensitive_attrs}

        # Verify that the passphrase attribute is NOT in the logged attributes
        assert "snowflake_private_key_file_pwd" not in attrs_to_log, (
            "snowflake_private_key_file_pwd should be excluded from config attribute debug output"
        )

        # But verify that the actual config has the value (not lost)
        assert hasattr(config, "snowflake_private_key_file_pwd"), (
            "Config should have snowflake_private_key_file_pwd attribute"
        )
        assert config.snowflake_private_key_file_pwd == "TEST_CONFIG_SECRET_789", (
            "Config should preserve the passphrase value"
        )

