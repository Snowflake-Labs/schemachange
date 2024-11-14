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
