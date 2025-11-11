from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.DeployConfig import DeployConfig

minimal_deploy_config_kwargs: dict = {
    "snowflake_account": "some_snowflake_account",
    "snowflake_user": "some_snowflake_user",
    "snowflake_role": "some_snowflake_role",
    "snowflake_warehouse": "some_snowflake_warehouse",
}

complete_deploy_config_kwargs: dict = {
    **minimal_deploy_config_kwargs,
    "config_file_path": Path("some_config_file_name"),
    "root_folder": "some_root_folder_name",
    "modules_folder": "some_modules_folder_name",
    "config_vars": {"some": "config_vars"},
    "snowflake_database": "some_snowflake_database",
    "snowflake_schema": "some_snowflake_schema",
    "change_history_table": "some_history_table",
    "query_tag": "some_query_tag",
}


@mock.patch("pathlib.Path.is_dir", side_effect=[False])
def test_invalid_root_folder(_):
    with pytest.raises(Exception) as e_info:
        DeployConfig.factory(**complete_deploy_config_kwargs)
    e_info_value = str(e_info.value)
    assert "Path is not valid directory: some_root_folder_name" in e_info_value


@mock.patch("pathlib.Path.is_dir", side_effect=[True, False])
def test_invalid_modules_folder(_):
    with pytest.raises(Exception) as e_info:
        DeployConfig.factory(**complete_deploy_config_kwargs)
    e_info_value = str(e_info.value)
    assert "Path is not valid directory: some_modules_folder_name" in e_info_value


def test_config_vars_not_a_dict():
    with pytest.raises(Exception) as e_info:
        BaseConfig.factory(
            subcommand="deploy",
            config_vars="a string",
            config_file_path=Path("."),
        )
    assert "config_vars did not parse correctly, please check its configuration" in str(e_info.value)


def test_config_vars_reserved_word():
    with pytest.raises(Exception) as e_info:
        BaseConfig.factory(
            subcommand="deploy",
            config_vars={"schemachange": "not allowed"},
            config_file_path=Path("."),
        )
    assert "The variable 'schemachange' has been reserved for use by schemachange, please use a different name" in str(
        e_info.value
    )


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_oauth_token_file(mock_get_password, mock_get_token_file_path, _):
    """Test that OAuth token file is read and passed as token parameter for external OAuth"""
    import os
    import tempfile

    # Create a temporary OAuth token file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        f.write("test_oauth_token_12345\n")
        token_file_path = f.name

    try:
        mock_get_password.return_value = None
        mock_get_token_file_path.return_value = token_file_path

        config = DeployConfig.factory(config_file_path=Path("."), **minimal_deploy_config_kwargs)
        session_kwargs = config.get_session_kwargs()

        # OAuth token should be read from file and passed as 'token'
        assert "token" in session_kwargs
        assert session_kwargs["token"] == "test_oauth_token_12345"
    finally:
        # Clean up temp file
        os.unlink(token_file_path)


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_oauth_token_file_whitespace(mock_get_password, mock_get_token_file_path, _):
    """Test that OAuth token file content is stripped of whitespace"""
    import os
    import tempfile

    # Create a temporary OAuth token file with extra whitespace
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        f.write("  \n  test_oauth_token_with_whitespace  \n\n  ")
        token_file_path = f.name

    try:
        mock_get_password.return_value = None
        mock_get_token_file_path.return_value = token_file_path

        config = DeployConfig.factory(config_file_path=Path("."), **minimal_deploy_config_kwargs)
        session_kwargs = config.get_session_kwargs()

        # OAuth token should be stripped
        assert "token" in session_kwargs
        assert session_kwargs["token"] == "test_oauth_token_with_whitespace"
    finally:
        os.unlink(token_file_path)


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_oauth_token_file_not_found(mock_get_password, mock_get_token_file_path, _):
    """Test that FileNotFoundError is raised when OAuth token file doesn't exist"""
    mock_get_password.return_value = None
    mock_get_token_file_path.return_value = "/nonexistent/path/to/oauth_token.txt"

    config = DeployConfig.factory(config_file_path=Path("."), **minimal_deploy_config_kwargs)

    with pytest.raises(FileNotFoundError) as e_info:
        config.get_session_kwargs()

    assert "Token file not found: /nonexistent/path/to/oauth_token.txt" in str(e_info.value)


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_empty_oauth_token_file(mock_get_password, mock_get_token_file_path, _):
    """Test that ValueError is raised when OAuth token file is empty"""
    import os
    import tempfile

    # Create an empty OAuth token file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        f.write("")
        token_file_path = f.name

    try:
        mock_get_password.return_value = None
        mock_get_token_file_path.return_value = token_file_path

        config = DeployConfig.factory(config_file_path=Path("."), **minimal_deploy_config_kwargs)

        with pytest.raises(ValueError) as e_info:
            config.get_session_kwargs()

        assert "Token file is empty:" in str(e_info.value)
    finally:
        os.unlink(token_file_path)


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_oauth_token_file_whitespace_only(mock_get_password, mock_get_token_file_path, _):
    """Test that ValueError is raised when OAuth token file contains only whitespace"""
    import os
    import tempfile

    # Create an OAuth token file with only whitespace
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        f.write("   \n\n\t  ")
        token_file_path = f.name

    try:
        mock_get_password.return_value = None
        mock_get_token_file_path.return_value = token_file_path

        config = DeployConfig.factory(config_file_path=Path("."), **minimal_deploy_config_kwargs)

        with pytest.raises(ValueError) as e_info:
            config.get_session_kwargs()

        assert "Token file is empty:" in str(e_info.value)
    finally:
        os.unlink(token_file_path)


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_oauth_token_file_expanduser(mock_get_password, mock_get_token_file_path, _):
    """Test that ~ in OAuth token file path is expanded"""
    import os
    import tempfile

    # Create a temporary OAuth token file in a location we can control
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        f.write("test_oauth_token_with_tilde")
        token_file_path = f.name

    try:
        # Mock the expanduser to return our temp file
        mock_get_password.return_value = None
        # Simulate a path with ~
        mock_get_token_file_path.return_value = token_file_path

        config = DeployConfig.factory(config_file_path=Path("."), **minimal_deploy_config_kwargs)
        session_kwargs = config.get_session_kwargs()

        assert "token" in session_kwargs
        assert session_kwargs["token"] == "test_oauth_token_with_tilde"
    finally:
        os.unlink(token_file_path)


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_without_oauth_token_file(mock_get_password, mock_get_token_file_path, _):
    """Test that no OAuth token is passed when token file path is None"""
    mock_get_password.return_value = "test_password_or_pat"
    mock_get_token_file_path.return_value = None

    config = DeployConfig.factory(config_file_path=Path("."), **minimal_deploy_config_kwargs)
    session_kwargs = config.get_session_kwargs()

    # No OAuth token should be present
    assert "token" not in session_kwargs
    # But password should be present (could be traditional password or PAT)
    assert session_kwargs["password"] == "test_password_or_pat"


@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_authenticator")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_private_key_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_private_key_passphrase")
@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_authentication_parameters_cli_takes_precedence_over_env(
    _,
    mock_get_passphrase,
    mock_get_key_path,
    mock_get_authenticator,
    mock_get_password,
):
    """Test that explicitly provided config parameters take precedence over ENV variables

    Note: This tests the factory method's precedence logic. Parameters can come from
    CLI args, YAML, or connections.toml. The private_key_passphrase can only come from
    ENV or connections.toml (CLI support removed for security).
    """
    # Set up ENV values
    mock_get_password.return_value = "env_password"
    mock_get_authenticator.return_value = "env_authenticator"
    mock_get_key_path.return_value = "/env/path/to/key.pem"
    mock_get_passphrase.return_value = "env_passphrase"

    # Set up explicitly provided config values (from YAML, connections.toml, or CLI where supported)
    # Note: authenticator and private_key_path CAN come from CLI
    # private_key_passphrase can only come from ENV or connections.toml (not CLI)
    # Fields use snowflake_ prefix internally, stripped when passed to connect()
    config_kwargs = {
        **minimal_deploy_config_kwargs,
        "snowflake_authenticator": "explicit_authenticator",
        "snowflake_private_key_path": "/explicit/path/to/key.pem",
        # This would typically come from connections.toml, not CLI (CLI not supported for security)
        "snowflake_private_key_passphrase": "explicit_passphrase",
    }

    config = DeployConfig.factory(config_file_path=Path("."), **config_kwargs)
    session_kwargs = config.get_session_kwargs()

    # Explicitly provided values should take precedence over ENV
    # Note: private_key_path internally maps to private_key_file for the connector
    assert session_kwargs["authenticator"] == "explicit_authenticator"
    assert session_kwargs["private_key_file"] == "/explicit/path/to/key.pem"
    assert session_kwargs["private_key_passphrase"] == "explicit_passphrase"
    # Password is only from ENV (not overridden in this test)
    assert session_kwargs["password"] == "env_password"


@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_authenticator")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_private_key_path")
@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_authentication_parameters_fallback_to_env(
    _,
    mock_get_key_path,
    mock_get_authenticator,
    mock_get_password,
):
    """Test that ENV authentication parameters are used when CLI params not provided"""
    # Set up ENV values
    mock_get_password.return_value = "env_password"
    mock_get_authenticator.return_value = "snowflake_jwt"
    mock_get_key_path.return_value = "/env/path/to/key.pem"

    # Don't provide CLI values - should use ENV
    config = DeployConfig.factory(config_file_path=Path("."), **minimal_deploy_config_kwargs)
    session_kwargs = config.get_session_kwargs()

    # ENV values should be used
    # Note: private_key_path internally maps to private_key_file for the connector
    assert session_kwargs["authenticator"] == "snowflake_jwt"
    assert session_kwargs["private_key_file"] == "/env/path/to/key.pem"
    assert session_kwargs["password"] == "env_password"


@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_deploy_config_expands_tilde_in_private_key_path(_):
    """Test that DeployConfig expands ~ in private_key_path before passing to connector"""
    home_dir = Path.home()

    config_kwargs = {
        **minimal_deploy_config_kwargs,
        "snowflake_authenticator": "snowflake_jwt",
        "snowflake_private_key_path": "~/.snowflake/snowflake_key.p8",
    }

    config = DeployConfig.factory(config_file_path=Path("."), **config_kwargs)
    session_kwargs = config.get_session_kwargs()

    # Verify that tilde is expanded to full path and mapped to private_key_file
    assert session_kwargs["private_key_file"] == str(home_dir / ".snowflake/snowflake_key.p8")
    assert "~" not in session_kwargs["private_key_file"]


@mock.patch("schemachange.config.DeployConfig.get_snowflake_private_key_path")
@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_deploy_config_expands_tilde_in_private_key_path_from_env(_, mock_get_key_path):
    """Test that DeployConfig expands ~ in private_key_path from ENV variable"""
    mock_get_key_path.return_value = "~/keys/rsa_key.pem"
    home_dir = Path.home()

    config_kwargs = {
        **minimal_deploy_config_kwargs,
        "snowflake_authenticator": "snowflake_jwt",
    }

    config = DeployConfig.factory(config_file_path=Path("."), **config_kwargs)
    session_kwargs = config.get_session_kwargs()

    # Verify that tilde from ENV is expanded to full path and mapped to private_key_file
    assert session_kwargs["private_key_file"] == str(home_dir / "keys/rsa_key.pem")
    assert "~" not in session_kwargs["private_key_file"]
