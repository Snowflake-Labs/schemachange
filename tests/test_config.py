from argparse import Namespace
from pathlib import Path
from unittest import mock

import pytest

from Config import Config, DeployConfig, config_factory, RenderConfig


@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_config_inject_config_file_path_no_config_folder(_):
    config = Config(subcommand="deploy")
    assert config.config_file_path == Path(".") / config.default_config_file_name


@mock.patch("pathlib.Path.is_dir", return_value=True)
def test_config_inject_config_file_path_with_config_folder(_):
    config_folder = "some_config_folder"
    config = Config(subcommand="deploy", config_folder=config_folder)
    assert (
        config.config_file_path == Path(config_folder) / config.default_config_file_name
    )


@mock.patch("pathlib.Path.is_dir", return_value=False)
def test_config_invalid_dirs(_):
    with pytest.raises(Exception) as e_info:
        Config(
            subcommand="deploy",
            config_folder="some_config_folder_name",
            root_folder="some_root_folder_name",
            modules_folder="some_modules_folder_name",
            vars={"some": "vars"},
            snowflake_account="some_snowflake_account",
            snowflake_user="some_snowflake_user",
            snowflake_role="some_snowflake_role",
            snowflake_warehouse="some_snowflake_warehouse",
            snowflake_database="some_snowflake_database",
            snowflake_schema="some_snowflake_schema",
            change_history_table="some_history_table",
            query_tag="some_query_tag",
            oauth_config={"some": "values"},
            version_number_validation_regex="some_regex",
        )
    e_info_value = str(e_info.value)
    assert "Invalid config_folder folder: some_config_folder_name" in e_info_value
    assert "Invalid root_folder folder: some_root_folder_name" in e_info_value
    assert "Invalid modules_folder folder: some_modules_folder_name" in e_info_value


def test_config_vars_not_a_dict():
    with pytest.raises(Exception) as e_info:
        Config(subcommand="deploy", vars="a string")
    assert (
        "Value error, vars did not parse correctly, please check its configuration"
        in str(e_info.value)
    )


def test_config_vars_reserved_word():
    with pytest.raises(Exception) as e_info:
        Config(subcommand="deploy", vars={"schemachange": "not allowed"})
    assert (
        "The variable 'schemachange' has been reserved for use by schemachange, please use a different name"
        in str(e_info.value)
    )


@pytest.mark.parametrize(
    "args, expected_class",
    [
        (Namespace(subcommand="deploy"), DeployConfig),
        (Namespace(subcommand="render", script="some script"), RenderConfig),
    ],
)
def test_config_factory(args: Namespace, expected_class: DeployConfig | RenderConfig):
    result = config_factory(args)
    # noinspection PyTypeChecker
    assert isinstance(result, expected_class)


def test_config_factory_unhandled_subcommand():
    with pytest.raises(Exception) as e_info:
        config_factory(Namespace(subcommand="unhandled"))
    assert "unhandled subcommand" in str(e_info)
