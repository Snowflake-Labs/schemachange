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
    assert "config_vars did not parse correctly, please check its configuration" in str(
        e_info.value
    )


def test_config_vars_reserved_word():
    with pytest.raises(Exception) as e_info:
        BaseConfig.factory(
            subcommand="deploy",
            config_vars={"schemachange": "not allowed"},
            config_file_path=Path("."),
        )
    assert (
        "The variable 'schemachange' has been reserved for use by schemachange, please use a different name"
        in str(e_info.value)
    )


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_oauth_token_file(
    mock_get_password, mock_get_token_file_path, _
):
    """Test that OAuth token file is read and passed as token parameter for external OAuth"""
    import tempfile
    import os

    # Create a temporary OAuth token file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        f.write("test_oauth_token_12345\n")
        token_file_path = f.name

    try:
        mock_get_password.return_value = None
        mock_get_token_file_path.return_value = token_file_path

        config = DeployConfig.factory(
            config_file_path=Path("."), **minimal_deploy_config_kwargs
        )
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
def test_get_session_kwargs_with_oauth_token_file_whitespace(
    mock_get_password, mock_get_token_file_path, _
):
    """Test that OAuth token file content is stripped of whitespace"""
    import tempfile
    import os

    # Create a temporary OAuth token file with extra whitespace
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        f.write("  \n  test_oauth_token_with_whitespace  \n\n  ")
        token_file_path = f.name

    try:
        mock_get_password.return_value = None
        mock_get_token_file_path.return_value = token_file_path

        config = DeployConfig.factory(
            config_file_path=Path("."), **minimal_deploy_config_kwargs
        )
        session_kwargs = config.get_session_kwargs()

        # OAuth token should be stripped
        assert "token" in session_kwargs
        assert session_kwargs["token"] == "test_oauth_token_with_whitespace"
    finally:
        os.unlink(token_file_path)


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_oauth_token_file_not_found(
    mock_get_password, mock_get_token_file_path, _
):
    """Test that FileNotFoundError is raised when OAuth token file doesn't exist"""
    mock_get_password.return_value = None
    mock_get_token_file_path.return_value = "/nonexistent/path/to/oauth_token.txt"

    config = DeployConfig.factory(
        config_file_path=Path("."), **minimal_deploy_config_kwargs
    )

    with pytest.raises(FileNotFoundError) as e_info:
        config.get_session_kwargs()

    assert "Token file not found: /nonexistent/path/to/oauth_token.txt" in str(
        e_info.value
    )


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_empty_oauth_token_file(
    mock_get_password, mock_get_token_file_path, _
):
    """Test that ValueError is raised when OAuth token file is empty"""
    import tempfile
    import os

    # Create an empty OAuth token file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        f.write("")
        token_file_path = f.name

    try:
        mock_get_password.return_value = None
        mock_get_token_file_path.return_value = token_file_path

        config = DeployConfig.factory(
            config_file_path=Path("."), **minimal_deploy_config_kwargs
        )

        with pytest.raises(ValueError) as e_info:
            config.get_session_kwargs()

        assert "Token file is empty:" in str(e_info.value)
    finally:
        os.unlink(token_file_path)


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_oauth_token_file_whitespace_only(
    mock_get_password, mock_get_token_file_path, _
):
    """Test that ValueError is raised when OAuth token file contains only whitespace"""
    import tempfile
    import os

    # Create an OAuth token file with only whitespace
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        f.write("   \n\n\t  ")
        token_file_path = f.name

    try:
        mock_get_password.return_value = None
        mock_get_token_file_path.return_value = token_file_path

        config = DeployConfig.factory(
            config_file_path=Path("."), **minimal_deploy_config_kwargs
        )

        with pytest.raises(ValueError) as e_info:
            config.get_session_kwargs()

        assert "Token file is empty:" in str(e_info.value)
    finally:
        os.unlink(token_file_path)


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_with_oauth_token_file_expanduser(
    mock_get_password, mock_get_token_file_path, _
):
    """Test that ~ in OAuth token file path is expanded"""
    import tempfile
    import os

    # Create a temporary OAuth token file in a location we can control
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".token") as f:
        f.write("test_oauth_token_with_tilde")
        token_file_path = f.name

    try:
        # Mock the expanduser to return our temp file
        mock_get_password.return_value = None
        # Simulate a path with ~
        mock_get_token_file_path.return_value = token_file_path

        config = DeployConfig.factory(
            config_file_path=Path("."), **minimal_deploy_config_kwargs
        )
        session_kwargs = config.get_session_kwargs()

        assert "token" in session_kwargs
        assert session_kwargs["token"] == "test_oauth_token_with_tilde"
    finally:
        os.unlink(token_file_path)


@mock.patch("pathlib.Path.is_dir", return_value=True)
@mock.patch("schemachange.config.DeployConfig.get_snowflake_token_file_path")
@mock.patch("schemachange.config.DeployConfig.get_snowflake_password")
def test_get_session_kwargs_without_oauth_token_file(
    mock_get_password, mock_get_token_file_path, _
):
    """Test that no OAuth token is passed when token file path is None"""
    mock_get_password.return_value = "test_password_or_pat"
    mock_get_token_file_path.return_value = None

    config = DeployConfig.factory(
        config_file_path=Path("."), **minimal_deploy_config_kwargs
    )
    session_kwargs = config.get_session_kwargs()

    # No OAuth token should be present
    assert "token" not in session_kwargs
    # But password should be present (could be traditional password or PAT)
    assert session_kwargs["password"] == "test_password_or_pat"
