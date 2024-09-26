from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.DeployConfig import DeployConfig
from schemachange.config.RenderConfig import RenderConfig
from schemachange.config.utils import get_config_secrets


@pytest.fixture
@mock.patch("pathlib.Path.is_dir", return_value=True)
def yaml_config(_) -> DeployConfig:
    return DeployConfig.factory(
        config_file_path=Path(__file__).parent.parent.parent
        / "demo"
        / "basics_demo"
        / "schemachange-config.yml",
        root_folder=Path(__file__).parent.parent.parent / "demo" / "basics_demo",
        modules_folder=Path(__file__).parent.parent.parent / "demo" / "basics_demo",
        config_vars={"var1": "yaml_vars"},
        snowflake_account="yaml_snowflake_account",
        snowflake_user="yaml_snowflake_user",
        snowflake_role="yaml_snowflake_role",
        snowflake_warehouse="yaml_snowflake_warehouse",
        snowflake_database="yaml_snowflake_database",
        snowflake_schema="yaml_snowflake_schema",
        change_history_table="yaml_change_history_table",
        create_change_history_table=True,
        autocommit=True,
        dry_run=True,
        query_tag="yaml_query_tag",
        oauth_config={"oauth": "yaml_oauth"},
        version_number_validation_regex="yaml_version_number_validation_regex",
        raise_exception_on_ignored_versioned_script=True,
    )


class TestGetConfigSecrets:
    def test_given_empty_config_should_not_error(self):
        get_config_secrets(config_vars={})

    def test_given_none_should_not_error(self):
        get_config_secrets(None)

    @pytest.mark.parametrize(
        "config_vars, secret",
        [
            ({"secret": "secret_val1"}, "secret_val1"),
            ({"SECret": "secret_val2"}, "secret_val2"),
            ({"secret_key": "secret_val3"}, "secret_val3"),
            ({"s3_bucket_secret": "secret_val4"}, "secret_val4"),
            ({"s3SecretKey": "secret_val5"}, "secret_val5"),
            ({"nested": {"s3_bucket_secret": "secret_val6"}}, "secret_val6"),
        ],
    )
    def test_given__vars_with_keys_should_extract_secret(self, config_vars, secret):
        results = get_config_secrets(config_vars)
        assert secret in results

    def test_given_vars_with_secrets_key_then_all_children_should_be_treated_as_secrets(
        self,
    ):
        config_vars = {
            "secrets": {
                "database_name": "database_name_val",
                "schema_name": "schema_name_val",
                "nested_secrets": {"SEC_ONE": "SEC_ONE_VAL"},
            }
        }
        results = get_config_secrets(config_vars=config_vars)

        assert len(results) == 3
        assert "database_name_val" in results
        assert "schema_name_val" in results
        assert "SEC_ONE_VAL" in results

    def test_given_vars_with_nested_secrets_key_then_all_children_should_be_treated_as_secrets(
        self,
    ):
        config_vars = {
            "nested": {
                "secrets": {
                    "database_name": "database_name_val",
                    "schema_name": "schema_name_val",
                    "nested": {"SEC_ONE": "SEC_ONE_VAL"},
                }
            }
        }

        results = get_config_secrets(config_vars)

        assert len(results) == 3
        assert "database_name_val" in results
        assert "schema_name_val" in results
        assert "SEC_ONE_VAL" in results

    def test_given_vars_with_same_secret_twice_then_only_extracted_once(self):
        config_vars = {
            "secrets": {
                "database_name": "SECRET_VALUE",
                "schema_name": "SECRET_VALUE",
                "nested_secrets": {"SEC_ONE": "SECRET_VALUE"},
            }
        }

        results = get_config_secrets(config_vars)

        assert len(results) == 1
        assert "SECRET_VALUE" in results


class TestTable:
    @pytest.mark.parametrize(
        "table_str, expected",
        [
            (
                "DATABASE_NAME.SCHEMA_NAME.TABLE_NAME",
                ChangeHistoryTable(
                    table_name="TABLE_NAME",
                    schema_name="SCHEMA_NAME",
                    database_name="DATABASE_NAME",
                ),
            ),
            (
                "SCHEMA_NAME.TABLE_NAME",
                ChangeHistoryTable(
                    table_name="TABLE_NAME",
                    schema_name="SCHEMA_NAME",
                    database_name="METADATA",
                ),
            ),
            (
                "TABLE_NAME",
                ChangeHistoryTable(
                    table_name="TABLE_NAME",
                    schema_name="SCHEMACHANGE",
                    database_name="METADATA",
                ),
            ),
        ],
    )
    def test_from_str_happy_path(self, table_str: str, expected: ChangeHistoryTable):
        result = ChangeHistoryTable.from_str(table_str)
        assert result == expected

    def test_from_str_exception(self):
        with pytest.raises(ValueError) as e:
            ChangeHistoryTable.from_str("FOUR.THREE.TWO.ONE")

        assert "Invalid change history table name:" in str(e.value)

    @pytest.mark.parametrize(
        "table, expected",
        [
            (
                ChangeHistoryTable(
                    table_name="TABLE_NAME",
                    schema_name="SCHEMA_NAME",
                    database_name="DATABASE_NAME",
                ),
                "DATABASE_NAME.SCHEMA_NAME.TABLE_NAME",
            ),
            (
                ChangeHistoryTable(
                    table_name="TABLE_NAME",
                    schema_name="SCHEMA_NAME",
                    database_name="METADATA",
                ),
                "METADATA.SCHEMA_NAME.TABLE_NAME",
            ),
            (
                ChangeHistoryTable(
                    table_name="TABLE_NAME",
                    schema_name="SCHEMACHANGE",
                    database_name="METADATA",
                ),
                "METADATA.SCHEMACHANGE.TABLE_NAME",
            ),
        ],
    )
    def test_fully_qualified(self, table: ChangeHistoryTable, expected: str):
        result = table.fully_qualified
        assert result == expected


class TestConfig:
    @mock.patch("pathlib.Path.is_dir", side_effect=[False])
    def test_invalid_root_folder(self, _):
        with pytest.raises(Exception) as e_info:
            DeployConfig.factory(
                config_file_path=Path("some_config_file_name"),
                root_folder="some_root_folder_name",
                modules_folder="some_modules_folder_name",
                config_vars={"some": "config_vars"},
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
        assert "Path is not valid directory: some_root_folder_name" in e_info_value

    @mock.patch("pathlib.Path.is_dir", side_effect=[True, False])
    def test_invalid_modules_folder(self, _):
        with pytest.raises(Exception) as e_info:
            DeployConfig.factory(
                config_file_path=Path("some_config_file_name"),
                root_folder="some_root_folder_name",
                modules_folder="some_modules_folder_name",
                config_vars={"some": "config_vars"},
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
        assert "Path is not valid directory: some_modules_folder_name" in e_info_value

    def test_config_vars_not_a_dict(self):
        with pytest.raises(Exception) as e_info:
            BaseConfig.factory(
                subcommand="deploy",
                config_vars="a string",
                config_file_path=Path("."),
            )
        assert (
            "config_vars did not parse correctly, please check its configuration"
            in str(e_info.value)
        )

    def test_config_vars_reserved_word(self):
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

    def test_check_for_deploy_args_happy_path(self):
        config = DeployConfig.factory(
            snowflake_account="account",
            snowflake_user="user",
            snowflake_role="role",
            snowflake_warehouse="warehouse",
            config_file_path=Path("."),
        )
        config.check_for_deploy_args()

    def test_check_for_deploy_args_exception(self):
        config = DeployConfig.factory(config_file_path=Path("."))
        with pytest.raises(ValueError) as e:
            config.check_for_deploy_args()

        assert "Missing config values. The following config values are required" in str(
            e.value
        )


@mock.patch("pathlib.Path.is_file", return_value=False)
def test_render_config_invalid_path(_):
    with pytest.raises(Exception) as e_info:
        RenderConfig.factory(script_path="invalid path")
    assert "invalid file path" in str(e_info)
