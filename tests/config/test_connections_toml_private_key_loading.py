"""
Test that private key authentication parameters are correctly loaded from connections.toml

This test verifies that both NEW (private_key_file, private_key_file_pwd) and LEGACY
(private_key_path, private_key_passphrase) parameter names are correctly extracted from
connections.toml and passed to the Snowflake connector.

Regression test for: https://github.com/Snowflake-Labs/schemachange/issues/388
where authentication failed with "Password was not given but private key is encrypted"
because the NEW parameter names were missing from the well_known_params list in
get_merged_config.py, causing them to be lost during config loading.

Test coverage:
- NEW parameter names load correctly from connections.toml
- LEGACY parameter names still work (backward compatibility)
- Both verify and deploy commands handle them identically
- Parameters go to correct config attributes (not additional_snowflake_params)
"""

import sys
from unittest.mock import patch

import structlog

from schemachange.config.get_merged_config import get_merged_config


class TestConnectionsTomlPrivateKeyLoading:
    """Test that private key authentication parameters are correctly extracted from connections.toml."""

    def test_private_key_file_pwd_loaded_from_connections_toml(self, tmp_path):
        """
        Test that private_key_file_pwd from connections.toml is correctly loaded into config.

        This is the core bug in issue #388: private_key_file_pwd was not in the well_known_params list,
        so it wasn't being extracted from connections.toml and prefixed with snowflake_.
        """
        # Create a connections.toml with the NEW parameter names
        connections_file = tmp_path / "connections.toml"
        connections_file.write_text(
            """
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
"""
        )

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

        with patch.object(sys, "argv", test_args):
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
        connections_file.write_text(
            """
[test_connection]
account = "test_account"
user = "test_user"
role = "test_role"
warehouse = "test_warehouse"
private_key_file = "/path/to/my/key.p8"
private_key_file_pwd = "my_passphrase"
"""
        )

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

        with patch.object(sys, "argv", test_args):
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
        This test ensures we maintain backward compatibility during the deprecation period.
        """
        # Create a connections.toml with LEGACY parameter name
        connections_file = tmp_path / "connections.toml"
        connections_file.write_text(
            """
[test_connection]
account = "test_account"
user = "test_user"
role = "test_role"
warehouse = "test_warehouse"
private_key_path = "/legacy/path/key.p8"
private_key_passphrase = "LEGACY_PASSPHRASE"
"""
        )

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

        with patch.object(sys, "argv", test_args):
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

        This ensures the deprecation path works correctly: users can have both in their
        connections.toml during migration, and the new name will be used.
        """
        # Create a connections.toml with BOTH old and new names
        connections_file = tmp_path / "connections.toml"
        connections_file.write_text(
            """
[test_connection]
account = "test_account"
user = "test_user"
role = "test_role"
warehouse = "test_warehouse"
private_key_path = "/old/path/key.p8"
private_key_file = "/new/path/key.p8"
private_key_passphrase = "OLD_PASSPHRASE"
private_key_file_pwd = "NEW_PASSPHRASE"
"""
        )

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

        with patch.object(sys, "argv", test_args):
            config = get_merged_config(logger=logger)

        session_kwargs = config.get_session_kwargs()

        # The NEW parameter names should take precedence
        assert session_kwargs["private_key_file"] == "/new/path/key.p8", (
            "NEW private_key_file should take precedence over LEGACY private_key_path"
        )
        assert session_kwargs["private_key_file_pwd"] == "NEW_PASSPHRASE", (
            "NEW private_key_file_pwd should take precedence over LEGACY private_key_passphrase"
        )

    def test_verify_and_deploy_load_identically_from_connections_toml(self, tmp_path):
        """
        Test that BOTH verify and deploy load private_key_file_pwd identically from connections.toml.

        This is the exact scenario reported in issue #388: user reported verify working
        but deploy failing with the same connections.toml configuration.

        This test proves both commands use the same config loading code.
        """
        # Create a connections.toml with NEW recommended parameters
        connections_file = tmp_path / "connections.toml"
        connections_file.write_text(
            """
[myconnection]
account = "test_account"
user = "test_user"
role = "test_role"
warehouse = "test_warehouse"
authenticator = "snowflake_jwt"
private_key_file = "~/.ssh/snowflake_key.p8"
private_key_file_pwd = "SHARED_SECRET_PASSPHRASE"
"""
        )

        # Create config file
        config_file = tmp_path / "schemachange.yml"
        config_file.write_text("config-version: 1\n")

        # Create root folder
        root_folder = tmp_path / "migrations"
        root_folder.mkdir()

        # Test VERIFY command
        verify_args = [
            "schemachange",
            "verify",
            f"--config-file={config_file}",
            f"--root-folder={root_folder}",
            f"--connections-file-path={connections_file}",
            "--connection-name=myconnection",
        ]

        logger = structlog.get_logger()

        with patch.object(sys, "argv", verify_args):
            verify_config = get_merged_config(logger=logger)

        # Test DEPLOY command
        deploy_args = [
            "schemachange",
            "deploy",
            f"--config-file={config_file}",
            f"--root-folder={root_folder}",
            f"--connections-file-path={connections_file}",
            "--connection-name=myconnection",
        ]

        with patch.object(sys, "argv", deploy_args):
            deploy_config = get_merged_config(logger=logger)

        # Get session kwargs from both
        verify_kwargs = verify_config.get_session_kwargs()
        deploy_kwargs = deploy_config.get_session_kwargs()

        # CRITICAL: Both must have loaded the passphrase
        assert "private_key_file_pwd" in verify_kwargs, (
            "BUG: verify failed to load private_key_file_pwd from connections.toml! This is issue #388."
        )
        assert "private_key_file_pwd" in deploy_kwargs, (
            "BUG: deploy failed to load private_key_file_pwd from connections.toml! This is issue #388."
        )

        # CRITICAL: Values must be IDENTICAL
        assert verify_kwargs["private_key_file_pwd"] == "SHARED_SECRET_PASSPHRASE"
        assert deploy_kwargs["private_key_file_pwd"] == "SHARED_SECRET_PASSPHRASE"
        assert verify_kwargs["private_key_file_pwd"] == deploy_kwargs["private_key_file_pwd"], (
            "CRITICAL BUG: verify and deploy have DIFFERENT passphrase values! "
            "This is the exact bug from issue #388 where verify worked but deploy failed."
        )

        # Verify both loaded the same private_key_file path
        assert verify_kwargs.get("private_key_file") == deploy_kwargs.get("private_key_file"), (
            "verify and deploy should load identical private_key_file from connections.toml"
        )

    def test_passphrase_not_in_additional_snowflake_params(self, tmp_path):
        """
        Regression test for the ROOT CAUSE of issue #388.

        Before the fix, private_key_file_pwd ended up in additional_snowflake_params
        instead of being properly extracted as a well-known parameter. This test ensures
        the passphrase goes to the correct config attribute.
        """
        # Create connections.toml with NEW parameters
        connections_file = tmp_path / "connections.toml"
        connections_file.write_text(
            """
[myconnection]
account = "test_account"
user = "test_user"
private_key_file = "/path/to/key.p8"
private_key_file_pwd = "my_passphrase"
"""
        )

        # Create config file
        config_file = tmp_path / "schemachange.yml"
        config_file.write_text("config-version: 1\n")

        # Create root folder
        root_folder = tmp_path / "migrations"
        root_folder.mkdir()

        # Load config
        test_args = [
            "schemachange",
            "deploy",
            f"--config-file={config_file}",
            f"--root-folder={root_folder}",
            f"--connections-file-path={connections_file}",
            "--connection-name=myconnection",
        ]

        logger = structlog.get_logger()

        with patch.object(sys, "argv", test_args):
            config = get_merged_config(logger=logger)

        # CRITICAL: These should be in the MAIN config attributes, not additional_snowflake_params
        assert hasattr(config, "snowflake_private_key_file"), (
            "BUG: private_key_file not in config attributes! It's probably in additional_snowflake_params (wrong place)"
        )
        assert hasattr(config, "snowflake_private_key_file_pwd"), (
            "BUG: private_key_file_pwd not in config attributes! "
            "It's probably in additional_snowflake_params (wrong place). "
            "This is the ROOT CAUSE of issue #388."
        )

        # Verify they're NOT in additional_snowflake_params (wrong place)
        additional_params = config.additional_snowflake_params or {}
        assert "private_key_file" not in additional_params, (
            "BUG: private_key_file is in additional_snowflake_params! "
            "It should be extracted as a well-known parameter. "
            "This means it won't be passed to the connector correctly."
        )
        assert "private_key_file_pwd" not in additional_params, (
            "BUG: private_key_file_pwd is in additional_snowflake_params! "
            "It should be extracted as a well-known parameter. "
            "This is the ROOT CAUSE of issue #388 - the passphrase never reached the connector."
        )

        # Verify correct values
        assert config.snowflake_private_key_file == "/path/to/key.p8"
        assert config.snowflake_private_key_file_pwd == "my_passphrase"
