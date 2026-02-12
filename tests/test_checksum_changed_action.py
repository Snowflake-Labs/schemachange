"""
Tests for the checksum-changed-action feature.

This feature allows users to configure how schemachange handles versioned scripts
whose checksum has changed since they were applied:
- IGNORE (default): Log info and skip (current behavior)
- ERROR: Raise an exception and fail the deployment
- EXECUTE: Re-execute the modified script
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.ChecksumChangedAction import ChecksumChangedAction
from schemachange.config.DeployConfig import DeployConfig
from schemachange.deploy import deploy

minimal_deploy_config_kwargs: dict = {
    "snowflake_account": "test_account",
    "snowflake_user": "test_user",
    "snowflake_role": "test_role",
    "snowflake_warehouse": "test_warehouse",
}


class TestChecksumChangedActionConfig:
    """Test checksum_changed_action configuration option."""

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_checksum_changed_action_defaults_to_ignore(self, _):
        """Test that checksum_changed_action defaults to IGNORE for backward compatibility."""
        config = DeployConfig.factory(
            config_file_path=Path("."),
            **minimal_deploy_config_kwargs,
        )
        assert config.checksum_changed_action == ChecksumChangedAction.IGNORE

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_checksum_changed_action_can_be_set_to_error(self, _):
        """Test that checksum_changed_action can be set to ERROR."""
        config = DeployConfig.factory(
            config_file_path=Path("."),
            checksum_changed_action=ChecksumChangedAction.ERROR,
            **minimal_deploy_config_kwargs,
        )
        assert config.checksum_changed_action == ChecksumChangedAction.ERROR

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_checksum_changed_action_can_be_set_to_execute(self, _):
        """Test that checksum_changed_action can be set to EXECUTE."""
        config = DeployConfig.factory(
            config_file_path=Path("."),
            checksum_changed_action=ChecksumChangedAction.EXECUTE,
            **minimal_deploy_config_kwargs,
        )
        assert config.checksum_changed_action == ChecksumChangedAction.EXECUTE


class TestChecksumChangedActionDeployLogic:
    """Test the deploy logic with checksum_changed_action."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock SnowflakeSession."""
        session = mock.MagicMock()
        session.account = "test_account"
        session.role = "test_role"
        session.warehouse = "test_warehouse"
        session.database = "test_database"
        session.schema = "test_schema"
        session.change_history_table.fully_qualified = "METADATA.SCHEMACHANGE.CHANGE_HISTORY"
        return session

    @pytest.fixture
    def mock_config_base(self):
        """Create base config kwargs."""
        return {
            "config_file_path": Path("."),
            "root_folder": Path("."),
            "dry_run": False,
            "create_change_history_table": False,
            "raise_exception_on_ignored_versioned_script": False,
            "config_vars": {},
            "modules_folder": None,
            **minimal_deploy_config_kwargs,
        }

    def _create_mock_script(self, name: str, version: str, content: str = "SELECT 1;"):
        """Helper to create a mock versioned script."""
        script = mock.MagicMock()
        script.name = name
        script.version = version
        script.type = "V"
        script.format = "SQL"
        script.file_path = Path(f"/migrations/{name}")
        return script, content

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    @mock.patch("schemachange.deploy.get_all_scripts_recursively")
    @mock.patch("schemachange.deploy.JinjaTemplateProcessor")
    def test_ignore_action_skips_modified_script(
        self, mock_jinja, mock_get_scripts, _, mock_session, mock_config_base
    ):
        """
        Test that with checksum_changed_action=IGNORE (default), a modified script
        is logged and skipped.
        """
        script_v100, original_content = self._create_mock_script("v1.0.0__init.sql", "1.0.0", "SELECT 1;")
        modified_content = "SELECT 2; -- modified"
        mock_get_scripts.return_value = {"v1.0.0__init.sql": script_v100}

        mock_processor = mock.MagicMock()
        mock_processor.render.return_value = modified_content
        mock_processor.relpath.return_value = "v1.0.0__init.sql"
        mock_jinja.return_value = mock_processor

        original_checksum = hashlib.sha224(original_content.encode("utf-8")).hexdigest()
        versioned_scripts = defaultdict(dict)
        versioned_scripts["v1.0.0__init.sql"] = {
            "version": "1.0.0",
            "script": "v1.0.0__init.sql",
            "checksum": original_checksum,
        }
        mock_session.get_script_metadata.return_value = (versioned_scripts, None, "1.0.0")

        config = DeployConfig.factory(
            checksum_changed_action=ChecksumChangedAction.IGNORE,
            **mock_config_base
        )

        deploy(config, mock_session)

        mock_session.apply_change_script.assert_not_called()

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    @mock.patch("schemachange.deploy.get_all_scripts_recursively")
    @mock.patch("schemachange.deploy.JinjaTemplateProcessor")
    def test_error_action_raises_on_modified_script(
        self, mock_jinja, mock_get_scripts, _, mock_session, mock_config_base
    ):
        """
        Test that with checksum_changed_action=ERROR, a modified script
        raises a ValueError.
        """
        script_v100, original_content = self._create_mock_script("v1.0.0__init.sql", "1.0.0", "SELECT 1;")
        modified_content = "SELECT 2; -- modified"
        mock_get_scripts.return_value = {"v1.0.0__init.sql": script_v100}

        mock_processor = mock.MagicMock()
        mock_processor.render.return_value = modified_content
        mock_processor.relpath.return_value = "v1.0.0__init.sql"
        mock_jinja.return_value = mock_processor

        original_checksum = hashlib.sha224(original_content.encode("utf-8")).hexdigest()
        versioned_scripts = defaultdict(dict)
        versioned_scripts["v1.0.0__init.sql"] = {
            "version": "1.0.0",
            "script": "v1.0.0__init.sql",
            "checksum": original_checksum,
        }
        mock_session.get_script_metadata.return_value = (versioned_scripts, None, "1.0.0")

        config = DeployConfig.factory(
            checksum_changed_action=ChecksumChangedAction.ERROR,
            **mock_config_base
        )

        with pytest.raises(ValueError) as exc_info:
            deploy(config, mock_session)

        assert "Checksum has changed for applied script" in str(exc_info.value)
        assert "v1.0.0__init.sql" in str(exc_info.value)
        assert original_checksum in str(exc_info.value)

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    @mock.patch("schemachange.deploy.get_all_scripts_recursively")
    @mock.patch("schemachange.deploy.JinjaTemplateProcessor")
    def test_execute_action_re_runs_modified_script(
        self, mock_jinja, mock_get_scripts, _, mock_session, mock_config_base
    ):
        """
        Test that with checksum_changed_action=EXECUTE, a modified script
        is re-executed.
        """
        script_v100, original_content = self._create_mock_script("v1.0.0__init.sql", "1.0.0", "SELECT 1;")
        modified_content = "SELECT 2; -- modified"
        mock_get_scripts.return_value = {"v1.0.0__init.sql": script_v100}

        mock_processor = mock.MagicMock()
        mock_processor.render.return_value = modified_content
        mock_processor.relpath.return_value = "v1.0.0__init.sql"
        mock_processor.prepare_for_execution.return_value = modified_content
        mock_jinja.return_value = mock_processor

        original_checksum = hashlib.sha224(original_content.encode("utf-8")).hexdigest()
        versioned_scripts = defaultdict(dict)
        versioned_scripts["v1.0.0__init.sql"] = {
            "version": "1.0.0",
            "script": "v1.0.0__init.sql",
            "checksum": original_checksum,
        }
        mock_session.get_script_metadata.return_value = (versioned_scripts, None, "1.0.0")

        config = DeployConfig.factory(
            checksum_changed_action=ChecksumChangedAction.EXECUTE,
            **mock_config_base
        )

        deploy(config, mock_session)

        mock_session.apply_change_script.assert_called_once()
        call_args = mock_session.apply_change_script.call_args
        assert call_args.kwargs["script"] == script_v100

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    @mock.patch("schemachange.deploy.get_all_scripts_recursively")
    @mock.patch("schemachange.deploy.JinjaTemplateProcessor")
    def test_unchanged_script_skipped_regardless_of_action(
        self, mock_jinja, mock_get_scripts, _, mock_session, mock_config_base
    ):
        """
        Test that a script with unchanged checksum is skipped regardless of
        checksum_changed_action setting.
        """
        script_v100, content = self._create_mock_script("v1.0.0__init.sql", "1.0.0", "SELECT 1;")
        mock_get_scripts.return_value = {"v1.0.0__init.sql": script_v100}

        mock_processor = mock.MagicMock()
        mock_processor.render.return_value = content
        mock_processor.relpath.return_value = "v1.0.0__init.sql"
        mock_jinja.return_value = mock_processor

        checksum = hashlib.sha224(content.encode("utf-8")).hexdigest()
        versioned_scripts = defaultdict(dict)
        versioned_scripts["v1.0.0__init.sql"] = {
            "version": "1.0.0",
            "script": "v1.0.0__init.sql",
            "checksum": checksum,
        }
        mock_session.get_script_metadata.return_value = (versioned_scripts, None, "1.0.0")

        for action in [ChecksumChangedAction.IGNORE, ChecksumChangedAction.ERROR, ChecksumChangedAction.EXECUTE]:
            mock_session.reset_mock()
            config = DeployConfig.factory(
                checksum_changed_action=action,
                **mock_config_base
            )

            deploy(config, mock_session)

            mock_session.apply_change_script.assert_not_called()


class TestChecksumChangedActionCLI:
    """Test CLI argument parsing for checksum_changed_action."""

    def test_checksum_changed_action_cli_argument_parsed_ignore(self):
        """Test that --schemachange-checksum-changed-action IGNORE is parsed correctly."""
        from schemachange.config.parse_cli_args import parse_cli_args

        args = parse_cli_args(["deploy", "--schemachange-checksum-changed-action", "IGNORE"])
        assert args.get("checksum_changed_action") == ChecksumChangedAction.IGNORE

    def test_checksum_changed_action_cli_argument_parsed_error(self):
        """Test that --schemachange-checksum-changed-action ERROR is parsed correctly."""
        from schemachange.config.parse_cli_args import parse_cli_args

        args = parse_cli_args(["deploy", "--schemachange-checksum-changed-action", "ERROR"])
        assert args.get("checksum_changed_action") == ChecksumChangedAction.ERROR

    def test_checksum_changed_action_cli_argument_parsed_execute(self):
        """Test that --schemachange-checksum-changed-action EXECUTE is parsed correctly."""
        from schemachange.config.parse_cli_args import parse_cli_args

        args = parse_cli_args(["deploy", "--schemachange-checksum-changed-action", "EXECUTE"])
        assert args.get("checksum_changed_action") == ChecksumChangedAction.EXECUTE

    def test_checksum_changed_action_cli_argument_absent(self):
        """Test that checksum_changed_action is None when not provided."""
        from schemachange.config.parse_cli_args import parse_cli_args

        args = parse_cli_args(["deploy"])
        assert args.get("checksum_changed_action") is None

    def test_checksum_changed_action_short_form(self):
        """Test that --checksum-changed-action (short form) works."""
        from schemachange.config.parse_cli_args import parse_cli_args

        args = parse_cli_args(["deploy", "--checksum-changed-action", "ERROR"])
        assert args.get("checksum_changed_action") == ChecksumChangedAction.ERROR


class TestChecksumChangedActionEnvVar:
    """Test environment variable for checksum_changed_action."""

    @mock.patch.dict("os.environ", {"SCHEMACHANGE_CHECKSUM_CHANGED_ACTION": "IGNORE"})
    def test_checksum_changed_action_env_var_ignore(self):
        """Test that SCHEMACHANGE_CHECKSUM_CHANGED_ACTION=IGNORE is parsed correctly."""
        from schemachange.config.utils import get_schemachange_config_from_env

        env_config = get_schemachange_config_from_env()
        assert env_config.get("checksum_changed_action") == ChecksumChangedAction.IGNORE

    @mock.patch.dict("os.environ", {"SCHEMACHANGE_CHECKSUM_CHANGED_ACTION": "ERROR"})
    def test_checksum_changed_action_env_var_error(self):
        """Test that SCHEMACHANGE_CHECKSUM_CHANGED_ACTION=ERROR is parsed correctly."""
        from schemachange.config.utils import get_schemachange_config_from_env

        env_config = get_schemachange_config_from_env()
        assert env_config.get("checksum_changed_action") == ChecksumChangedAction.ERROR

    @mock.patch.dict("os.environ", {"SCHEMACHANGE_CHECKSUM_CHANGED_ACTION": "EXECUTE"})
    def test_checksum_changed_action_env_var_execute(self):
        """Test that SCHEMACHANGE_CHECKSUM_CHANGED_ACTION=EXECUTE is parsed correctly."""
        from schemachange.config.utils import get_schemachange_config_from_env

        env_config = get_schemachange_config_from_env()
        assert env_config.get("checksum_changed_action") == ChecksumChangedAction.EXECUTE

    @mock.patch.dict("os.environ", {"SCHEMACHANGE_CHECKSUM_CHANGED_ACTION": "error"})
    def test_checksum_changed_action_env_var_case_insensitive(self):
        """Test that SCHEMACHANGE_CHECKSUM_CHANGED_ACTION is case-insensitive."""
        from schemachange.config.utils import get_schemachange_config_from_env

        env_config = get_schemachange_config_from_env()
        assert env_config.get("checksum_changed_action") == ChecksumChangedAction.ERROR

    @mock.patch.dict("os.environ", {"SCHEMACHANGE_CHECKSUM_CHANGED_ACTION": "INVALID"})
    def test_checksum_changed_action_env_var_invalid_raises(self):
        """Test that invalid SCHEMACHANGE_CHECKSUM_CHANGED_ACTION raises ValueError."""
        from schemachange.config.utils import get_schemachange_config_from_env

        with pytest.raises(ValueError) as exc_info:
            get_schemachange_config_from_env()

        assert "Invalid value in SCHEMACHANGE_CHECKSUM_CHANGED_ACTION" in str(exc_info.value)
        assert "IGNORE, ERROR, EXECUTE" in str(exc_info.value)

    @mock.patch.dict("os.environ", {}, clear=True)
    def test_checksum_changed_action_env_var_absent(self):
        """Test that checksum_changed_action is not present when env var is not set."""
        from schemachange.config.utils import get_schemachange_config_from_env

        env_config = get_schemachange_config_from_env()
        assert "checksum_changed_action" not in env_config


class TestChecksumChangedActionEnum:
    """Test the ChecksumChangedAction enum."""

    def test_enum_values(self):
        """Test that enum has correct values."""
        assert ChecksumChangedAction.IGNORE.value == "IGNORE"
        assert ChecksumChangedAction.ERROR.value == "ERROR"
        assert ChecksumChangedAction.EXECUTE.value == "EXECUTE"

    def test_enum_members(self):
        """Test that enum has exactly 3 members."""
        assert len(ChecksumChangedAction) == 3
        assert set(ChecksumChangedAction.__members__.keys()) == {"IGNORE", "ERROR", "EXECUTE"}
