"""
Test for issue #388: Verify that private_key_file_pwd is correctly loaded from connections.toml

This test verifies the fix in get_merged_config.py where private_key_file_pwd and private_key_file
were missing from the well_known_params list, causing them to be lost when loading from connections.toml.
"""

from unittest.mock import patch

import structlog

from schemachange.config.get_merged_config import get_merged_config


class TestIssue388ConnectionsTomlLoading:
    """Test that private_key_file_pwd is correctly extracted from connections.toml."""

    def test_private_key_file_pwd_loaded_from_connections_toml(self, tmp_path):
        """
        Test that private_key_file_pwd from connections.toml is correctly loaded into DeployConfig.

        This is the core bug in issue #388: private_key_file_pwd was not in the well_known_params list,
        so it wasn't being extracted from connections.toml and prefixed with snowflake_.
        """
        # Create a connections.toml with the NEW parameter names
        connections_file = tmp_path / "connections.toml"
        connections_file.write_text("""
[test_connection]
account = "test_account"
user = "test_user"
role = "test_role"
warehouse = "test_warehouse"
database = "test_database"
schema = "test_schema"
authenticator = "snowflake_jwt"
private_key_file = "~/.ssh/snowflake_key.p8"
private_key_file_pwd = "SECRET_PASSPHRASE_FROM_TOML"
""")

        # Create a minimal schemachange config
        config_file = tmp_path / "schemachange.yml"
        config_file.write_text("config-version: 1\n")

        # Create a root folder
        root_folder = tmp_path / "migrations"
        root_folder.mkdir()

        # Mock sys.argv to simulate CLI args
        test_args = [
            "schemachange",
            "deploy",
            f"--config-file={config_file}",
            f"--root-folder={root_folder}",
            f"--connections-file-path={connections_file}",
            "--connection-name=test_connection",
        ]

        logger = structlog.get_logger()

        with patch("sys.argv", test_args):
            # Load the merged config
            config = get_merged_config(logger=logger)

        # CRITICAL ASSERTIONS: Verify the passphrase made it through
        assert hasattr(config, "snowflake_private_key_file_pwd"), (
            "Config should have snowflake_private_key_file_pwd attribute"
        )
        assert config.snowflake_private_key_file_pwd == "SECRET_PASSPHRASE_FROM_TOML", (
            "BUG: private_key_file_pwd from connections.toml was not loaded! "
            "Check that 'private_key_file_pwd' is in well_known_params list in get_merged_config.py"
        )

        # Verify it's in session_kwargs (what gets passed to snowflake.connector.connect)
        session_kwargs = config.get_session_kwargs()
        assert "private_key_file_pwd" in session_kwargs, "private_key_file_pwd should be in session_kwargs"
        assert session_kwargs["private_key_file_pwd"] == "SECRET_PASSPHRASE_FROM_TOML", (
            "Passphrase value should match what was in connections.toml"
        )

    def test_private_key_file_loaded_from_connections_toml(self, tmp_path):
        """
        Test that private_key_file (not just the passphrase) is also correctly loaded.

        The bug affected BOTH new parameter names: private_key_file and private_key_file_pwd.
        """
        # Create a connections.toml with private_key_file (new name)
        connections_file = tmp_path / "connections.toml"
        connections_file.write_text("""
[test_connection]
account = "test_account"
user = "test_user"
role = "test_role"
warehouse = "test_warehouse"
private_key_file = "/path/to/my/key.p8"
private_key_file_pwd = "my_passphrase"
""")

        # Create a minimal schemachange config
        config_file = tmp_path / "schemachange.yml"
        config_file.write_text("config-version: 1\n")

        # Create a root folder
        root_folder = tmp_path / "migrations"
        root_folder.mkdir()

        # Mock sys.argv
        test_args = [
            "schemachange",
            "deploy",
            f"--config-file={config_file}",
            f"--root-folder={root_folder}",
            f"--connections-file-path={connections_file}",
            "--connection-name=test_connection",
        ]

        logger = structlog.get_logger()

        with patch("sys.argv", test_args):
            config = get_merged_config(logger=logger)

        # Verify private_key_file made it through
        assert hasattr(config, "snowflake_private_key_file"), "Config should have snowflake_private_key_file attribute"
        assert config.snowflake_private_key_file == "/path/to/my/key.p8", (
            "BUG: private_key_file from connections.toml was not loaded! "
            "Check that 'private_key_file' is in well_known_params list in get_merged_config.py"
        )

        # Verify it's in session_kwargs
        session_kwargs = config.get_session_kwargs()
        assert "private_key_file" in session_kwargs, "private_key_file should be in session_kwargs"
        assert session_kwargs["private_key_file"] == "/path/to/my/key.p8", (
            "Private key file path should match what was in connections.toml"
        )

    def test_legacy_private_key_passphrase_still_works(self, tmp_path):
        """
        Test that the LEGACY parameter name (private_key_passphrase) still works.

        This was already in the well_known_params list, so it should have always worked.
        """
        # Create a connections.toml with LEGACY parameter name
        connections_file = tmp_path / "connections.toml"
        connections_file.write_text("""
[test_connection]
account = "test_account"
user = "test_user"
role = "test_role"
warehouse = "test_warehouse"
private_key_path = "/legacy/path/key.p8"
private_key_passphrase = "LEGACY_PASSPHRASE"
""")

        # Create a minimal schemachange config
        config_file = tmp_path / "schemachange.yml"
        config_file.write_text("config-version: 1\n")

        # Create a root folder
        root_folder = tmp_path / "migrations"
        root_folder.mkdir()

        # Mock sys.argv
        test_args = [
            "schemachange",
            "deploy",
            f"--config-file={config_file}",
            f"--root-folder={root_folder}",
            f"--connections-file-path={connections_file}",
            "--connection-name=test_connection",
        ]

        logger = structlog.get_logger()

        with patch("sys.argv", test_args):
            config = get_merged_config(logger=logger)

        # Legacy parameter should be mapped to the new internal name
        assert hasattr(config, "snowflake_private_key_passphrase"), (
            "Config should have snowflake_private_key_passphrase attribute (legacy)"
        )

        # Verify it's mapped to the new name in session_kwargs
        session_kwargs = config.get_session_kwargs()
        assert "private_key_file_pwd" in session_kwargs, (
            "Legacy passphrase should be mapped to private_key_file_pwd in session_kwargs"
        )
        assert session_kwargs["private_key_file_pwd"] == "LEGACY_PASSPHRASE", (
            "Passphrase value should be mapped from legacy name to new name"
        )

    def test_new_params_take_precedence_over_legacy(self, tmp_path):
        """
        Test that if BOTH old and new parameter names are present, the NEW one takes precedence.
        """
        # Create a connections.toml with BOTH old and new names
        connections_file = tmp_path / "connections.toml"
        connections_file.write_text("""
[test_connection]
account = "test_account"
user = "test_user"
role = "test_role"
warehouse = "test_warehouse"
private_key_path = "/old/path/key.p8"
private_key_file = "/new/path/key.p8"
private_key_passphrase = "OLD_PASSPHRASE"
private_key_file_pwd = "NEW_PASSPHRASE"
""")

        # Create a minimal schemachange config
        config_file = tmp_path / "schemachange.yml"
        config_file.write_text("config-version: 1\n")

        # Create a root folder
        root_folder = tmp_path / "migrations"
        root_folder.mkdir()

        # Mock sys.argv
        test_args = [
            "schemachange",
            "deploy",
            f"--config-file={config_file}",
            f"--root-folder={root_folder}",
            f"--connections-file-path={connections_file}",
            "--connection-name=test_connection",
        ]

        logger = structlog.get_logger()

        with patch("sys.argv", test_args):
            config = get_merged_config(logger=logger)

        session_kwargs = config.get_session_kwargs()

        # The NEW parameter names should take precedence
        assert session_kwargs["private_key_file"] == "/new/path/key.p8", (
            "NEW private_key_file should take precedence over LEGACY private_key_path"
        )
        assert session_kwargs["private_key_file_pwd"] == "NEW_PASSPHRASE", (
            "NEW private_key_file_pwd should take precedence over LEGACY private_key_passphrase"
        )
