from __future__ import annotations

from pathlib import Path
from unittest import mock

from schemachange.config.VerifyConfig import VerifyConfig

minimal_verify_config_kwargs: dict = {
    "snowflake_account": "some_snowflake_account",
    "snowflake_user": "some_snowflake_user",
    "snowflake_role": "some_snowflake_role",
    "snowflake_warehouse": "some_snowflake_warehouse",
}


@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_verify_config_factory(_):
    """Test that VerifyConfig.factory creates a valid config object"""
    config = VerifyConfig.factory(
        config_file_path=Path("."),
        **minimal_verify_config_kwargs,
    )

    assert config.subcommand == "verify"
    assert config.snowflake_account == "some_snowflake_account"
    assert config.snowflake_user == "some_snowflake_user"
    assert config.snowflake_role == "some_snowflake_role"
    assert config.snowflake_warehouse == "some_snowflake_warehouse"


@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_verify_config_get_session_kwargs(_):
    """Test that VerifyConfig.get_session_kwargs returns correct session parameters"""
    config = VerifyConfig.factory(
        config_file_path=Path("."),
        **minimal_verify_config_kwargs,
    )

    session_kwargs = config.get_session_kwargs()

    assert session_kwargs["account"] == "some_snowflake_account"
    assert session_kwargs["user"] == "some_snowflake_user"
    assert session_kwargs["role"] == "some_snowflake_role"
    assert session_kwargs["warehouse"] == "some_snowflake_warehouse"
    assert session_kwargs["autocommit"] is False


@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_verify_config_with_connection_name(_):
    """Test VerifyConfig with connections.toml settings"""
    config = VerifyConfig.factory(
        config_file_path=Path("."),
        connection_name="test_connection",
        connections_file_path=Path("/path/to/connections.toml"),
        **minimal_verify_config_kwargs,
    )

    session_kwargs = config.get_session_kwargs()

    assert session_kwargs["connection_name"] == "test_connection"
    assert session_kwargs["connections_file_path"] == Path("/path/to/connections.toml")


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.VerifyConfig.get_snowflake_password")
def test_verify_config_with_password(mock_get_password, _):
    """Test that VerifyConfig includes password from environment"""
    mock_get_password.return_value = "test_password"

    config = VerifyConfig.factory(
        config_file_path=Path("."),
        **minimal_verify_config_kwargs,
    )

    session_kwargs = config.get_session_kwargs()

    assert session_kwargs["password"] == "test_password"


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.VerifyConfig.get_snowflake_authenticator")
def test_verify_config_with_authenticator(mock_get_authenticator, _):
    """Test VerifyConfig with different authenticator"""
    mock_get_authenticator.return_value = "snowflake_jwt"

    config = VerifyConfig.factory(
        config_file_path=Path("."),
        **minimal_verify_config_kwargs,
    )

    session_kwargs = config.get_session_kwargs()

    assert session_kwargs["authenticator"] == "snowflake_jwt"


@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_verify_config_with_additional_params(_):
    """Test VerifyConfig with additional Snowflake connector parameters"""
    config = VerifyConfig.factory(
        config_file_path=Path("."),
        additional_snowflake_params={"client_session_keep_alive": True, "login_timeout": 60},
        **minimal_verify_config_kwargs,
    )

    session_kwargs = config.get_session_kwargs()

    assert session_kwargs["additional_snowflake_params"]["client_session_keep_alive"] is True
    assert session_kwargs["additional_snowflake_params"]["login_timeout"] == 60


@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_verify_config_cli_auth_takes_precedence_over_env(_):
    """Test that CLI authentication parameters take precedence over ENV variables"""
    with mock.patch("schemachange.config.VerifyConfig.get_snowflake_authenticator", return_value="env_auth"):
        with mock.patch("schemachange.config.VerifyConfig.get_snowflake_private_key_path", return_value="/env/key"):
            config = VerifyConfig.factory(
                config_file_path=Path("."),
                authenticator="cli_auth",
                private_key_path="/cli/key",
                **minimal_verify_config_kwargs,
            )

            session_kwargs = config.get_session_kwargs()

            # CLI values should take precedence
            assert session_kwargs["authenticator"] == "cli_auth"
            assert session_kwargs["private_key_path"] == "/cli/key"


@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_verify_config_filters_deployment_specific_params(_):
    """Test that VerifyConfig.factory filters out deployment-specific parameters"""
    # Create config with deployment-specific params (like would come from a deploy YAML config)
    config = VerifyConfig.factory(
        config_file_path=Path("."),
        change_history_table="SCHEMACHANGE_HISTORY",
        create_change_history_table=True,
        dry_run=True,
        autocommit=True,
        query_tag="test_query_tag",
        root_folder=Path("/some/root"),
        modules_folder=Path("/some/modules"),
        vars={"key": "value"},
        **minimal_verify_config_kwargs,
    )

    # Config should be created successfully without deployment params
    assert config.subcommand == "verify"
    assert config.snowflake_account == "some_snowflake_account"

    # Verify that deployment-specific attributes don't exist on VerifyConfig
    assert not hasattr(config, "change_history_table")
    assert not hasattr(config, "create_change_history_table")
    assert not hasattr(config, "dry_run")
    assert not hasattr(config, "query_tag")
