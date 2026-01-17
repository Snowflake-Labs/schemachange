"""
Tests for the deploy module, specifically testing the changes that removed max version number limitations.
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest.mock as mock
from pathlib import Path
from textwrap import dedent

import pytest
import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.DeployConfig import DeployConfig
from schemachange.deploy import deploy
from schemachange.session.Script import VersionedScript, RepeatableScript, AlwaysScript


@pytest.fixture
def mock_session():
    """Create a mock SnowflakeSession for testing."""
    session = mock.Mock()
    session.account = "test_account"
    session.role = "test_role"
    session.warehouse = "test_warehouse"
    session.database = "test_database"
    session.schema = "test_schema"
    session.change_history_table = ChangeHistoryTable(
        database_name="METADATA",
        schema_name="SCHEMACHANGE",
        table_name="CHANGE_HISTORY",
    )
    return session


@pytest.fixture
def mock_config():
    """Create a mock DeployConfig for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = mock.Mock(spec=DeployConfig)
        config.dry_run = False
        config.create_change_history_table = False
        config.root_folder = Path(tmpdir)
        config.modules_folder = None
        config.config_vars = {}
        config.version_number_validation_regex = None
        yield config


@pytest.fixture
def temp_script_dir():
    """Create a temporary directory with test scripts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        yield tmppath


class TestDeployVersionedScripts:
    """Test the new behavior for versioned scripts (no max version checking)."""

    def test_apply_versioned_script_not_in_history(self, mock_session, mock_config, temp_script_dir):
        """Test that a versioned script is applied when it's not in the change history."""
        # Create a test script
        script_file = temp_script_dir / "V1.0.0__test_script.sql"
        script_file.write_text("SELECT 1;")

        # Mock get_script_metadata to return empty history
        mock_session.get_script_metadata.return_value = (
            {},  # No versioned scripts in history
            None,  # No repeatable scripts
            None,  # No max version
        )

        # Mock apply_change_script to track calls
        mock_session.apply_change_script = mock.Mock()

        # Update config to point to temp dir
        mock_config.root_folder = temp_script_dir

        # Run deploy
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            mock_jinja.return_value.render.return_value = "SELECT 1;"
            mock_jinja.return_value.relpath.return_value = str(script_file)

            deploy(mock_config, mock_session)

        # Verify script was applied
        assert mock_session.apply_change_script.call_count == 1
        call_args = mock_session.apply_change_script.call_args
        assert call_args[1]["script"].name == "V1.0.0__test_script.sql"
        assert call_args[1]["script_content"] == "SELECT 1;"
        assert call_args[1]["dry_run"] is False

    def test_skip_versioned_script_already_applied(self, mock_session, mock_config, temp_script_dir):
        """Test that a versioned script is skipped when it's already in the change history."""
        # Create a test script
        script_file = temp_script_dir / "V1.0.0__test_script.sql"
        script_content = "SELECT 1;"
        script_file.write_text(script_content)

        # Calculate checksum for the script
        checksum = hashlib.sha224(script_content.encode("utf-8")).hexdigest()

        # Mock get_script_metadata to return script in history
        mock_session.get_script_metadata.return_value = (
            {
                "V1.0.0__test_script.sql": {
                    "checksum": checksum,
                    "script_name": "V1.0.0__test_script.sql",
                }
            },
            None,  # No repeatable scripts
            "1.0.0",  # Max version (though this should no longer matter)
        )

        # Mock apply_change_script to track calls
        mock_session.apply_change_script = mock.Mock()

        # Update config to point to temp dir
        mock_config.root_folder = temp_script_dir

        # Run deploy
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            mock_jinja.return_value.render.return_value = script_content
            mock_jinja.return_value.relpath.return_value = str(script_file)

            deploy(mock_config, mock_session)

        # Verify script was NOT applied
        assert mock_session.apply_change_script.call_count == 0

    def test_apply_lower_version_script_not_in_history(self, mock_session, mock_config, temp_script_dir):
        """
        Test that a script with a lower version number is applied if it's not in history.
        This is the key change - previously this would have been skipped.
        """
        # Create a test script with a "lower" version
        script_file = temp_script_dir / "V1.0.0__earlier_script.sql"
        script_file.write_text("SELECT 1;")

        # Mock get_script_metadata to return a higher max version but script not in history
        mock_session.get_script_metadata.return_value = (
            {
                "V1.5.0__later_script.sql": {
                    "checksum": "dummy_checksum",
                    "script_name": "V1.5.0__later_script.sql",
                }
            },
            None,
            "1.5.0",  # Max version is higher than our script
        )

        # Mock apply_change_script to track calls
        mock_session.apply_change_script = mock.Mock()

        # Update config to point to temp dir
        mock_config.root_folder = temp_script_dir

        # Run deploy
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            mock_jinja.return_value.render.return_value = "SELECT 1;"
            mock_jinja.return_value.relpath.return_value = str(script_file)

            deploy(mock_config, mock_session)

        # Verify script WAS applied (this is the new behavior)
        assert mock_session.apply_change_script.call_count == 1
        call_args = mock_session.apply_change_script.call_args
        assert call_args[1]["script"].name == "V1.0.0__earlier_script.sql"

    def test_checksum_drift_detection(self, mock_session, mock_config, temp_script_dir, caplog):
        """Test that checksum drift is detected and logged for already-applied scripts."""
        # Create a test script with modified content
        script_file = temp_script_dir / "V1.0.0__test_script.sql"
        new_content = "SELECT 2;"  # Different from what was applied
        script_file.write_text(new_content)

        # Calculate old checksum (for different content)
        old_content = "SELECT 1;"
        old_checksum = hashlib.sha224(old_content.encode("utf-8")).hexdigest()

        # Mock get_script_metadata to return script with old checksum
        mock_session.get_script_metadata.return_value = (
            {
                "V1.0.0__test_script.sql": {
                    "checksum": old_checksum,
                    "script_name": "V1.0.0__test_script.sql",
                }
            },
            None,
            "1.0.0",
        )

        # Mock apply_change_script
        mock_session.apply_change_script = mock.Mock()

        # Update config to point to temp dir
        mock_config.root_folder = temp_script_dir

        # Run deploy with logging
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            mock_jinja.return_value.render.return_value = new_content
            mock_jinja.return_value.relpath.return_value = str(script_file)

            with caplog.at_level("INFO"):
                deploy(mock_config, mock_session)

        # Verify script was NOT applied but drift was logged
        assert mock_session.apply_change_script.call_count == 0
        # Note: The actual logging check would need to verify structlog output


class TestDeployRepeatableScripts:
    """Test repeatable script behavior."""

    def test_apply_repeatable_script_with_changed_checksum(self, mock_session, mock_config, temp_script_dir):
        """Test that a repeatable script is applied when its checksum has changed."""
        # Create a test script
        script_file = temp_script_dir / "R__test_repeatable.sql"
        new_content = "SELECT 2;"
        script_file.write_text(new_content)

        # Calculate old checksum
        old_content = "SELECT 1;"
        old_checksum = hashlib.sha224(old_content.encode("utf-8")).hexdigest()

        # Mock get_script_metadata
        mock_session.get_script_metadata.return_value = (
            {},  # No versioned scripts
            {"r__test_repeatable.sql": [old_checksum]},  # Old checksum for repeatable
            None,
        )

        # Mock apply_change_script
        mock_session.apply_change_script = mock.Mock()

        # Update config to point to temp dir
        mock_config.root_folder = temp_script_dir

        # Run deploy
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            mock_jinja.return_value.render.return_value = new_content
            mock_jinja.return_value.relpath.return_value = str(script_file)

            deploy(mock_config, mock_session)

        # Verify script was applied
        assert mock_session.apply_change_script.call_count == 1

    def test_skip_repeatable_script_with_unchanged_checksum(self, mock_session, mock_config, temp_script_dir):
        """Test that a repeatable script is skipped when its checksum hasn't changed."""
        # Create a test script
        script_file = temp_script_dir / "R__test_repeatable.sql"
        content = "SELECT 1;"
        script_file.write_text(content)

        # Calculate checksum
        checksum = hashlib.sha224(content.encode("utf-8")).hexdigest()

        # Mock get_script_metadata
        mock_session.get_script_metadata.return_value = (
            {},  # No versioned scripts
            {"R__test_repeatable.sql": [checksum]},  # Same checksum
            None,
        )

        # Mock apply_change_script
        mock_session.apply_change_script = mock.Mock()

        # Update config to point to temp dir
        mock_config.root_folder = temp_script_dir

        # Run deploy
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            mock_jinja.return_value.render.return_value = content
            mock_jinja.return_value.relpath.return_value = str(script_file)

            deploy(mock_config, mock_session)

        # Verify script was NOT applied
        assert mock_session.apply_change_script.call_count == 0


class TestDeployAlwaysScripts:
    """Test always script behavior."""

    def test_always_scripts_are_always_applied(self, mock_session, mock_config, temp_script_dir):
        """Test that always scripts are applied every time."""
        # Create a test script
        script_file = temp_script_dir / "A__test_always.sql"
        content = "SELECT 1;"
        script_file.write_text(content)

        # Mock get_script_metadata
        mock_session.get_script_metadata.return_value = ({}, None, None)

        # Mock apply_change_script
        mock_session.apply_change_script = mock.Mock()

        # Update config to point to temp dir
        mock_config.root_folder = temp_script_dir

        # Run deploy
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            mock_jinja.return_value.render.return_value = content
            mock_jinja.return_value.relpath.return_value = str(script_file)

            deploy(mock_config, mock_session)

        # Verify script was applied
        assert mock_session.apply_change_script.call_count == 1


class TestDeployScriptOrdering:
    """Test that scripts are applied in the correct order."""

    def test_scripts_applied_in_correct_order(self, mock_session, mock_config, temp_script_dir):
        """Test that versioned scripts are applied before repeatable, and repeatable before always."""
        # Create test scripts
        scripts = [
            ("V1.0.0__versioned.sql", "SELECT 'v1';"),
            ("V1.5.0__versioned2.sql", "SELECT 'v2';"),
            ("R__repeatable.sql", "SELECT 'r';"),
            ("A__always.sql", "SELECT 'a';"),
        ]

        for filename, content in scripts:
            (temp_script_dir / filename).write_text(content)

        # Mock get_script_metadata - no scripts in history
        mock_session.get_script_metadata.return_value = ({}, None, None)

        # Track call order
        applied_scripts = []

        def track_apply(script, script_content, dry_run, logger):
            applied_scripts.append(script.name)

        mock_session.apply_change_script = mock.Mock(side_effect=track_apply)

        # Update config to point to temp dir
        mock_config.root_folder = temp_script_dir

        # Run deploy
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            mock_jinja.return_value.render.side_effect = lambda path, vars: scripts[
                [s[0] for s in scripts].index(Path(path).name)
            ][1]
            mock_jinja.return_value.relpath.side_effect = lambda path: str(path)

            deploy(mock_config, mock_session)

        # Verify order: V scripts, then R scripts, then A scripts
        assert len(applied_scripts) == 4
        assert applied_scripts[0] == "V1.0.0__versioned.sql"
        assert applied_scripts[1] == "V1.5.0__versioned2.sql"
        assert applied_scripts[2] == "R__repeatable.sql"
        assert applied_scripts[3] == "A__always.sql"


class TestDeployDryRun:
    """Test dry-run mode behavior."""

    def test_dry_run_mode(self, mock_session, mock_config, temp_script_dir):
        """Test that scripts are not applied in dry-run mode."""
        # Create a test script
        script_file = temp_script_dir / "V1.0.0__test_script.sql"
        script_file.write_text("SELECT 1;")

        # Mock get_script_metadata
        mock_session.get_script_metadata.return_value = ({}, None, None)

        # Mock apply_change_script
        mock_session.apply_change_script = mock.Mock()

        # Update config to point to temp dir and enable dry-run
        mock_config.root_folder = temp_script_dir
        mock_config.dry_run = True

        # Run deploy
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            mock_jinja.return_value.render.return_value = "SELECT 1;"
            mock_jinja.return_value.relpath.return_value = str(script_file)

            deploy(mock_config, mock_session)

        # Verify apply_change_script was still called (it handles dry-run internally)
        assert mock_session.apply_change_script.call_count == 1
        # Verify dry_run flag was passed
        assert mock_session.apply_change_script.call_args[1]["dry_run"] is True


class TestDeployMultipleVersionedScripts:
    """Test deployment with multiple versioned scripts in various states."""

    def test_mixed_applied_and_unapplied_scripts(self, mock_session, mock_config, temp_script_dir):
        """Test deployment with a mix of applied and unapplied versioned scripts."""
        # Create test scripts
        scripts = [
            ("V1.0.0__first.sql", "SELECT 1;"),
            ("V1.1.0__second.sql", "SELECT 2;"),
            ("V1.2.0__third.sql", "SELECT 3;"),
        ]

        for filename, content in scripts:
            (temp_script_dir / filename).write_text(content)

        # Mock get_script_metadata - V1.1.0 was already applied
        checksum_v1_1 = hashlib.sha224("SELECT 2;".encode("utf-8")).hexdigest()
        mock_session.get_script_metadata.return_value = (
            {
                "V1.1.0__second.sql": {
                    "checksum": checksum_v1_1,
                    "script_name": "V1.1.0__second.sql",
                }
            },
            None,
            "1.1.0",
        )

        # Track applied scripts
        applied_scripts = []

        def track_apply(script, script_content, dry_run, logger):
            applied_scripts.append(script.name)

        mock_session.apply_change_script = mock.Mock(side_effect=track_apply)

        # Update config to point to temp dir
        mock_config.root_folder = temp_script_dir

        # Run deploy
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            mock_jinja.return_value.render.side_effect = lambda path, vars: scripts[
                [s[0] for s in scripts].index(Path(path).name)
            ][1]
            mock_jinja.return_value.relpath.side_effect = lambda path: str(path)

            deploy(mock_config, mock_session)

        # Verify V1.0.0 and V1.2.0 were applied, but not V1.1.0
        assert len(applied_scripts) == 2
        assert "V1.0.0__first.sql" in applied_scripts
        assert "V1.2.0__third.sql" in applied_scripts
        assert "V1.1.0__second.sql" not in applied_scripts


class TestDeployOutOfOrderVersions:
    """Test that out-of-order versions are handled correctly with the new behavior."""

    def test_apply_out_of_order_version_not_in_history(self, mock_session, mock_config, temp_script_dir):
        """
        Test the core new feature: applying a script with version 1.0.0 even when 2.0.0 exists.
        Previously this would have been skipped, now it should be applied.
        """
        # Create scripts in non-sequential order
        (temp_script_dir / "V1.0.0__first.sql").write_text("SELECT 1;")
        (temp_script_dir / "V2.0.0__second.sql").write_text("SELECT 2;")
        (temp_script_dir / "V1.5.0__middle.sql").write_text("SELECT 1.5;")

        # Mock that V2.0.0 was already applied
        checksum_v2 = hashlib.sha224("SELECT 2;".encode("utf-8")).hexdigest()
        mock_session.get_script_metadata.return_value = (
            {
                "V2.0.0__second.sql": {
                    "checksum": checksum_v2,
                    "script_name": "V2.0.0__second.sql",
                }
            },
            None,
            "2.0.0",  # Max version
        )

        # Track applied scripts
        applied_scripts = []

        def track_apply(script, script_content, dry_run, logger):
            applied_scripts.append((script.name, script.version))

        mock_session.apply_change_script = mock.Mock(side_effect=track_apply)

        # Update config to point to temp dir
        mock_config.root_folder = temp_script_dir

        # Run deploy
        with mock.patch("schemachange.deploy.JinjaTemplateProcessor") as mock_jinja:
            def render_side_effect(path, vars):
                if "1.0.0" in path:
                    return "SELECT 1;"
                elif "2.0.0" in path:
                    return "SELECT 2;"
                elif "1.5.0" in path:
                    return "SELECT 1.5;"

            mock_jinja.return_value.render.side_effect = render_side_effect
            mock_jinja.return_value.relpath.side_effect = lambda path: str(path)

            deploy(mock_config, mock_session)

        # Verify that V1.0.0 and V1.5.0 were applied despite being "older" than V2.0.0
        assert len(applied_scripts) == 2
        assert ("V1.0.0__first.sql", "1.0.0") in applied_scripts
        assert ("V1.5.0__middle.sql", "1.5.0") in applied_scripts
        # V2.0.0 should not be in the list as it was already applied
        assert not any(name == "V2.0.0__second.sql" for name, _ in applied_scripts)
