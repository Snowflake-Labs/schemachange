"""
Test that verify and deploy commands use IDENTICAL authentication code paths.

This is a regression test for issue #388 where users reported verify working
but deploy failing with the same configuration.

These tests verify that when authentication parameters are passed directly to
VerifyConfig and DeployConfig, both produce identical session_kwargs.

NOTE: Tests for connections.toml loading are in tests/config/test_issue388_connections_toml.py
because connections.toml loading happens in get_merged_config(), not in the factory() methods.
"""

import pytest

from schemachange.config.DeployConfig import DeployConfig
from schemachange.config.VerifyConfig import VerifyConfig


class TestVerifyDeployAuthEquivalence:
    """Ensure verify and deploy handle authentication identically when parameters are passed directly."""

    @pytest.mark.parametrize(
        "auth_params",
        [
            pytest.param(
                # Test case 1: Private key with NEW parameter names (issue #388 scenario)
                {
                    "snowflake_account": "test_account",
                    "snowflake_user": "test_user",
                    "snowflake_role": "test_role",
                    "snowflake_warehouse": "test_warehouse",
                    "snowflake_authenticator": "snowflake_jwt",
                    "snowflake_private_key_file": "/path/to/key.p8",
                    "snowflake_private_key_file_pwd": "my_secret_passphrase",
                },
                id="private_key_with_new_parameter_names",
            ),
            pytest.param(
                # Test case 2: Private key with LEGACY parameter names
                {
                    "snowflake_account": "test_account",
                    "snowflake_user": "test_user",
                    "snowflake_private_key_path": "/path/to/key.p8",
                    "snowflake_private_key_passphrase": "my_secret_passphrase",
                },
                id="private_key_with_legacy_parameter_names",
            ),
        ],
    )
    def test_verify_and_deploy_produce_identical_session_kwargs(self, tmp_path, auth_params):
        """
        Test that verify and deploy produce IDENTICAL session_kwargs for authentication.

        This test verifies that the get_session_kwargs() implementation is identical
        in both VerifyConfig and DeployConfig. This proves that both commands handle
        authentication parameters the same way.

        For connections.toml loading tests, see tests/config/test_issue388_connections_toml.py
        """
        # Create minimal config file
        config_file = tmp_path / "schemachange.yml"
        config_file.write_text("config-version: 1\n")

        # Create root folder (needed for deploy)
        root_folder = tmp_path / "migrations"
        root_folder.mkdir()

        # Create VerifyConfig with authentication parameters
        verify_config = VerifyConfig.factory(
            config_file_path=config_file,
            root_folder=root_folder,
            **auth_params,
        )

        # Create DeployConfig with same authentication parameters
        deploy_config = DeployConfig.factory(
            config_file_path=config_file,
            root_folder=root_folder,
            **auth_params,
        )

        # Get session kwargs from both
        verify_kwargs = verify_config.get_session_kwargs()
        deploy_kwargs = deploy_config.get_session_kwargs()

        # Authentication-related parameters that MUST be identical
        auth_related_keys = [
            "account",
            "user",
            "role",
            "warehouse",
            "authenticator",
            "private_key_file",
            "private_key_file_pwd",
        ]

        # Compare authentication parameters
        for key in auth_related_keys:
            verify_value = verify_kwargs.get(key)
            deploy_value = deploy_kwargs.get(key)

            assert verify_value == deploy_value, (
                f"AUTHENTICATION DIFFERENCE FOUND for '{key}':\n"
                f"  verify: {verify_value}\n"
                f"  deploy: {deploy_value}\n"
                f"This means verify and deploy handle authentication differently!\n"
                f"This is the bug reported in issue #388."
            )
