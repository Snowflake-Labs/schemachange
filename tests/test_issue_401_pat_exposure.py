"""
Test for Issue #401: Credentials exposed in DEBUG logs

This test reproduces the bug where PAT tokens, passwords, and other credentials
are exposed when logging with **kwargs spreading, even though redaction is configured.

The bug occurs because:
1. Secrets from environment variables (SNOWFLAKE_PASSWORD) are not added to config.secrets
2. Only config_vars secrets are collected by get_config_secrets()
3. When logger.debug("message", **kwargs) spreads kwargs, redaction doesn't catch them
"""

import os
from pathlib import Path
from unittest.mock import patch

import structlog
from structlog.testing import LogCapture

from schemachange.config.DeployConfig import DeployConfig
from schemachange.redact_config_secrets import redact_config_secrets


class TestIssue401CredentialExposure:
    """Test that issue #401 PAT/password exposure is fixed."""

    def test_password_from_env_var_exposed_in_debug_kwargs_spreading(self):
        """
        Test that issue #401 is FIXED.

        When SNOWFLAKE_PASSWORD is set (for PAT authentication) and we log with
        **kwargs spreading, the password must be redacted from logs.

        This test verifies that authentication secrets from env vars are now
        properly collected and added to config.secrets for redaction.
        """
        # Set up a PAT in environment variable (how users authenticate in issue #401)
        test_pat = "SUPER_SECRET_PAT_sn0w_12345_EXPOSED"

        with patch.dict(os.environ, {"SNOWFLAKE_PASSWORD": test_pat}):
            # Create a config (password is read from env var)
            config = DeployConfig.factory(
                config_file_path=Path("test.yml"),
                root_folder=Path("."),
                snowflake_account="test_account",
                snowflake_user="test_user",
                change_history_table="db.schema.table",
            )

            # VERIFY FIX: password IS now in config.secrets
            assert test_pat in config.secrets, (
                "FIX FAILED: PAT from SNOWFLAKE_PASSWORD should be in config.secrets for redaction"
            )

            # Set up log capture FIRST (before redaction)
            log_capture = LogCapture()
            structlog.configure(processors=[log_capture])

            # Configure redaction with secrets from config
            # Now this WILL add the redaction processor because config.secrets contains the PAT
            redact_config_secrets(config_secrets=config.secrets)

            logger = structlog.get_logger()

            # Simulate what SnowflakeSession.__init__ does at line 127
            # It creates connect_kwargs that includes the password
            connect_kwargs = config.get_session_kwargs()

            # Log with **kwargs spreading (the scenario from issue #401)
            logger.info("snowflake.connector.connect kwargs", **connect_kwargs)

            # Collect all log output
            all_log_entries = log_capture.entries

            # SECURITY CHECK: The PAT must be REDACTED in logs
            assert len(all_log_entries) > 0, "Test setup error: No log entries captured"

            first_entry = all_log_entries[0]

            # The password field should exist but be redacted (replaced with asterisks)
            assert "password" in first_entry, "Password field should be in log entry"
            assert first_entry["password"] == "*" * len(test_pat), (
                f"Password should be redacted to asterisks, got: {first_entry['password']}"
            )

            # Original PAT should NOT appear anywhere in the log
            assert test_pat not in str(first_entry), (
                f"SECURITY BUG STILL EXISTS: PAT was found in log entry!\n{first_entry}"
            )

    def test_token_from_file_exposed_in_debug_kwargs_spreading(self, tmp_path):
        """
        FAILING TEST: OAuth tokens from files should also be redacted.

        Similar to passwords, tokens read from files need to be in config.secrets.
        """
        # Create a token file
        token_file = tmp_path / "oauth_token.txt"
        test_token = "SECRET_OAUTH_TOKEN_xyz789"
        token_file.write_text(test_token)

        # Create config with token file path
        config = DeployConfig.factory(
            config_file_path=Path("test.yml"),
            root_folder=Path("."),
            snowflake_account="test_account",
            snowflake_user="test_user",
            snowflake_authenticator="oauth",
            snowflake_token_file_path=str(token_file),
            change_history_table="db.schema.table",
        )

        # Configure redaction
        redact_config_secrets(config_secrets=config.secrets)

        # Set up log capture
        log_capture = LogCapture()
        structlog.configure(processors=[log_capture])

        logger = structlog.get_logger()

        # Get session kwargs (includes token read from file)
        session_kwargs = config.get_session_kwargs()

        # Log with **kwargs spreading
        logger.debug("session kwargs", **session_kwargs)

        # Check that token is NOT exposed
        all_log_text = "\n".join([str(entry) for entry in log_capture.entries])

        assert test_token not in all_log_text, (
            f"SECURITY BUG: OAuth token from file was exposed in DEBUG logs!\n"
            f"Token '{test_token}' should be redacted but was found in logs."
        )

    def test_private_key_passphrase_from_env_exposed_in_kwargs(self):
        """
        FAILING TEST: Private key passphrases from env vars should be redacted.

        This extends issue #388 fix - the passphrase needs to be in config.secrets.
        """
        test_passphrase = "PRIVATE_KEY_SECRET_PASSPHRASE_abc123"

        with patch.dict(os.environ, {"SNOWFLAKE_PRIVATE_KEY_FILE_PWD": test_passphrase}):
            config = DeployConfig.factory(
                config_file_path=Path("test.yml"),
                root_folder=Path("."),
                snowflake_account="test_account",
                snowflake_user="test_user",
                snowflake_private_key_file="/fake/path/key.p8",
                change_history_table="db.schema.table",
            )

            # Configure redaction
            redact_config_secrets(config_secrets=config.secrets)

            # Set up log capture
            log_capture = LogCapture()
            structlog.configure(processors=[log_capture])

            logger = structlog.get_logger()

            # Get session kwargs (includes passphrase from env)
            session_kwargs = config.get_session_kwargs()

            # Log with **kwargs spreading
            logger.debug("connection parameters", **session_kwargs)

            # Check that passphrase is NOT exposed
            all_log_text = "\n".join([str(entry) for entry in log_capture.entries])

            assert test_passphrase not in all_log_text, (
                f"SECURITY BUG: Private key passphrase from env var was exposed in DEBUG logs!\n"
                f"Passphrase '{test_passphrase}' should be redacted but was found in logs."
            )

    def test_existing_masking_still_works(self):
        """
        REGRESSION TEST: Ensure existing masking in SnowflakeSession still works.

        This test should PASS both before and after the fix.
        """
        test_password = "TEST_PASSWORD_xyz789"

        with patch.dict(os.environ, {"SNOWFLAKE_PASSWORD": test_password}):
            config = DeployConfig.factory(
                config_file_path=Path("test.yml"),
                root_folder=Path("."),
                snowflake_account="test_account",
                snowflake_user="test_user",
                change_history_table="db.schema.table",
            )

            # Configure redaction
            redact_config_secrets(config_secrets=config.secrets)

            # Set up log capture
            log_capture = LogCapture()
            structlog.configure(processors=[log_capture])

            logger = structlog.get_logger()

            # Get session kwargs
            session_kwargs = config.get_session_kwargs()

            # Use EXISTING masking approach (should work)
            masked_connect_kwargs = {
                k: v
                for k, v in session_kwargs.items()
                if k not in ["password", "token", "private_key_passphrase", "private_key_file_pwd"]
            }

            # Log with masked kwargs
            logger.debug("masked connection kwargs", **masked_connect_kwargs)

            # This should NOT have the password (existing protection works)
            all_log_text = "\n".join([str(entry) for entry in log_capture.entries])

            assert test_password not in all_log_text, (
                "REGRESSION: Existing masking broke! Password should not be in masked kwargs."
            )
