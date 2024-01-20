from argparse import Namespace
from pathlib import Path
from unittest import mock

import pytest

from schemachange.Config import (
    Config,
    DeployConfig,
    config_factory,
    RenderConfig,
    Table,
)


@pytest.fixture
@mock.patch("pathlib.Path.is_dir", return_value=True)
def yaml_config(_) -> DeployConfig:
    return DeployConfig(
        config_folder=Path("yaml_config_folder"),
        root_folder=Path("yaml_root_folder"),
        modules_folder=Path("yaml_modules_folder"),
        vars={"var1": "yaml_vars"},
        snowflake_account="yaml_snowflake_account",
        snowflake_user="yaml_snowflake_user",
        snowflake_role="yaml_snowflake_role",
        snowflake_warehouse="yaml_snowflake_warehouse",
        snowflake_database="yaml_snowflake_database",
        snowflake_schema="yaml_snowflake_schema",
        change_history_table=Table(table_name="yaml_change_history_table"),
        create_change_history_table=True,
        autocommit=True,
        dry_run=True,
        query_tag="yaml_query_tag",
        oauth_config={"oauth": "yaml_oauth"},
        version_number_validation_regex="yaml_version_number_validation_regex",
        raise_exception_on_ignored_versioned_migration=True,
    )


class TestConfig:
    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_inject_config_file_path_no_config_folder(self, _):
        config = Config(subcommand="deploy")
        assert config.config_file_path == Path(".") / config.default_config_file_name

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_inject_config_file_path_with_config_folder(self, _):
        config_folder = "some_config_folder"
        config = Config(subcommand="deploy", config_folder=config_folder)
        assert (
            config.config_file_path
            == Path(config_folder) / config.default_config_file_name
        )

    @mock.patch("pathlib.Path.is_dir", return_value=False)
    def test_invalid_dirs(self, _):
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
                change_history_table=Table(table_name="some_history_table"),
                query_tag="some_query_tag",
                oauth_config={"some": "values"},
                version_number_validation_regex="some_regex",
            )
        e_info_value = str(e_info.value)
        assert "Invalid config_folder folder: some_config_folder_name" in e_info_value
        assert "Invalid root_folder folder: some_root_folder_name" in e_info_value
        assert "Invalid modules_folder folder: some_modules_folder_name" in e_info_value

    def test_vars_not_a_dict(self):
        with pytest.raises(Exception) as e_info:
            Config(subcommand="deploy", vars="a string")
        assert (
            "Value error, vars did not parse correctly, please check its configuration"
            in str(e_info.value)
        )

    def test_vars_reserved_word(self):
        with pytest.raises(Exception) as e_info:
            Config(subcommand="deploy", vars={"schemachange": "not allowed"})
        assert (
            "The variable 'schemachange' has been reserved for use by schemachange, please use a different name"
            in str(e_info.value)
        )

    @pytest.mark.parametrize(
        "cli_config, cli_overrides",
        [
            (DeployConfig(), []),
            (
                DeployConfig(
                    config_folder=Path(".") / "assets",
                    root_folder=Path(".") / "assets",
                    modules_folder=Path(".") / "assets",
                    vars={"var1": "cli_vars"},
                    snowflake_account="cli_snowflake_account",
                    snowflake_user="cli_snowflake_user",
                    snowflake_role="cli_snowflake_role",
                    snowflake_warehouse="cli_snowflake_warehouse",
                    snowflake_database="cli_snowflake_database",
                    snowflake_schema="cli_snowflake_schema",
                    change_history_table=Table(table_name="cli_change_history_table"),
                    create_change_history_table=False,
                    autocommit=False,
                    dry_run=False,
                    query_tag="cli_query_tag",
                    oauth_config={"oauth": "cli_oauth"},
                    version_number_validation_regex="cli_version_number_validation_regex",
                    raise_exception_on_ignored_versioned_migration=False,
                ),
                [
                    "config_folder",
                    "root_folder",
                    "modules_folder",
                    "vars",
                    "snowflake_account",
                    "snowflake_user",
                    "snowflake_role",
                    "snowflake_warehouse",
                    "snowflake_database",
                    "snowflake_schema",
                    "change_history_table",
                    "create_change_history_table",
                    "autocommit",
                    "dry_run",
                    "query_tag",
                    "oauth_config",
                    "version_number_validation_regex",
                    "raise_exception_on_ignored_versioned_migration",
                ],
            ),
        ],
    )
    def test_merge_exclude_unset(
        self,
        yaml_config: DeployConfig,
        cli_config: DeployConfig,
        cli_overrides: list[str],
    ):
        merged_config = yaml_config.merge_exclude_unset(other=cli_config)

        for name, field in merged_config.model_fields.items():
            if name not in cli_overrides:
                assert getattr(merged_config, name) == getattr(yaml_config, name)
            else:
                assert getattr(merged_config, name) == getattr(cli_config, name)


@pytest.mark.parametrize(
    "args, expected_class",
    [
        (Namespace(subcommand="deploy"), DeployConfig),
        (Namespace(subcommand="render", script_path="some script"), RenderConfig),
    ],
)
@mock.patch("pathlib.Path.is_file", return_value=True)
def test_config_factory(
    _, args: Namespace, expected_class: DeployConfig | RenderConfig
):
    result = config_factory(args)
    # noinspection PyTypeChecker
    assert isinstance(result, expected_class)


def test_config_factory_unhandled_subcommand():
    with pytest.raises(Exception) as e_info:
        config_factory(Namespace(subcommand="unhandled"))
    assert "unhandled subcommand" in str(e_info)


@mock.patch("pathlib.Path.is_file", return_value=False)
def test_render_config_invalid_path(_):
    with pytest.raises(Exception) as e_info:
        RenderConfig(script_path="invalid path")
    assert "invalid script_path" in str(e_info)
