"""
Test that private key content passed through to the connector is never exposed in logs.

The connector's private_key parameter can reach schemachange through the generic
SNOWFLAKE_* environment variable pass-through (SNOWFLAKE_PRIVATE_KEY) or the YAML v2
snowflake section (private-key). Neither path was covered by the existing redaction,
so the key content was printed in the DEBUG "snowflake.connector.connect kwargs" line.
"""

from pathlib import Path
from unittest import mock

import pytest
import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.DeployConfig import DeployConfig
from schemachange.config.utils import _parse_yaml_v2
from schemachange.session.SnowflakeSession import SnowflakeSession

FAKE_KEY = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC_FAKE_TEST_KEY"


class TestPrivateKeyContentRedaction:
    @pytest.mark.parametrize("param_name", ["private_key", "private-key"])
    def test_connect_kwargs_debug_log_excludes_private_key(self, param_name):
        """The key must reach the connector but never appear in the connect kwargs log line."""
        logger = structlog.testing.CapturingLogger()

        with mock.patch("snowflake.connector.connect") as mock_connect:
            with mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string"):
                # noinspection PyTypeChecker
                SnowflakeSession(
                    user="user",
                    account="account",
                    schemachange_version="4.4.0",
                    application="schemachange",
                    change_history_table=ChangeHistoryTable(),
                    logger=logger,
                    additional_snowflake_params={param_name: FAKE_KEY, "authenticator": "snowflake_jwt"},
                )

        assert mock_connect.call_args.kwargs["private_key"] == FAKE_KEY

        all_log_text = "\n".join(str(call) for call in logger.calls)
        assert FAKE_KEY not in all_log_text, f"Private key content was exposed in logs:\n{all_log_text}"

    @pytest.mark.parametrize("param_name", ["private_key", "private-key"])
    def test_private_key_content_is_added_to_config_secrets(self, param_name):
        """The key value must be registered for redaction wherever it might be logged."""
        config = DeployConfig.factory(
            config_file_path=Path("schemachange-config.yml"),
            root_folder=Path("."),
            additional_snowflake_params={param_name: FAKE_KEY},
        )

        assert FAKE_KEY in config.secrets

    def test_no_private_key_adds_no_secret(self):
        config = DeployConfig.factory(
            config_file_path=Path("schemachange-config.yml"),
            root_folder=Path("."),
            additional_snowflake_params={"login_timeout": 30},
        )

        assert "30" not in config.secrets

    def test_yaml_v2_private_key_triggers_security_warning(self):
        raw_config = {
            "config-version": 2,
            "snowflake": {"account": "account", "private-key": FAKE_KEY},
        }

        with pytest.warns(UserWarning, match="private-key"):
            _parse_yaml_v2(raw_config)


class TestPrivateKeyContentPassThrough:
    def _connect(self, **kwargs):
        logger = structlog.testing.CapturingLogger()
        with mock.patch("snowflake.connector.connect") as mock_connect:
            with mock.patch("schemachange.session.SnowflakeSession.get_snowflake_identifier_string"):
                # noinspection PyTypeChecker
                SnowflakeSession(
                    user="user",
                    account="account",
                    schemachange_version="4.4.0",
                    application="schemachange",
                    change_history_table=ChangeHistoryTable(),
                    logger=logger,
                    **kwargs,
                )
        return mock_connect.call_args.kwargs, logger

    def test_file_and_content_are_both_passed_to_the_connector(self):
        # The connector decides what to do when both are set (v5 rejects it with a clear error)
        connect_kwargs, logger = self._connect(
            private_key_file="/path/to/key.p8",
            additional_snowflake_params={"private_key": FAKE_KEY},
        )

        assert connect_kwargs["private_key_file"] == "/path/to/key.p8"
        assert connect_kwargs["private_key"] == FAKE_KEY
        assert FAKE_KEY not in str(logger.calls)

    def test_content_only_is_passed_without_warning(self):
        connect_kwargs, logger = self._connect(additional_snowflake_params={"private_key": FAKE_KEY})

        assert connect_kwargs["private_key"] == FAKE_KEY
        assert not [call for call in logger.calls if call.method_name == "warning"]

    def test_file_only_is_passed_without_warning(self):
        connect_kwargs, logger = self._connect(private_key_file="/path/to/key.p8")

        assert connect_kwargs["private_key_file"] == "/path/to/key.p8"
        assert "private_key" not in connect_kwargs
        assert not [call for call in logger.calls if call.method_name == "warning"]
