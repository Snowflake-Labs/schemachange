from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.get_merged_config import get_merged_config

required_args = [
    "--snowflake-account",
    "account",
    "--snowflake-user",
    "user",
    "--snowflake-warehouse",
    "warehouse",
    "--snowflake-role",
    "role",
]


class TestGetMergedConfig:
    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_default_config_folder(self, _):
        with mock.patch("sys.argv", ["schemachange", *required_args]):
            config = get_merged_config()
            assert (
                config.config_file_path == Path(".") / config.default_config_file_name
            )

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_config_folder(self, _):
        with mock.patch(
            "sys.argv", ["schemachange", "--config-folder", "DUMMY", *required_args]
        ):
            config = get_merged_config()
            assert (
                config.config_file_path
                == Path("DUMMY") / config.default_config_file_name
            )

    @mock.patch("pathlib.Path.is_dir", return_value=False)
    def test_invalid_config_folder(self, _):
        with pytest.raises(Exception) as e_info:
            with mock.patch(
                "sys.argv", ["schemachange", "--config-folder", "DUMMY", *required_args]
            ):
                config = get_merged_config()
                assert (
                    config.config_file_path
                    == Path("DUMMY") / config.default_config_file_name
                )
        e_info_value = str(e_info.value)
        assert "Path is not valid directory: DUMMY" in e_info_value

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_no_cli_args(self, _):
        with mock.patch(
            "sys.argv", ["schemachange", "--config-folder", str(Path(__file__).parent)]
        ):
            config = get_merged_config()

            assert config.snowflake_account == "snowflake-account-from-yaml"
            assert config.snowflake_user == "snowflake-user-from-yaml"
            assert config.snowflake_warehouse == '"snowflake-warehouse-from-yaml"'
            assert config.snowflake_role == '"snowflake-role-from-yaml"'
            assert str(config.root_folder) == "root-folder-from-yaml"
            assert str(config.modules_folder) == "modules-folder-from-yaml"
            assert config.snowflake_database == '"snowflake-database-from-yaml"'
            assert config.snowflake_schema == '"snowflake-schema-from-yaml"'
            assert config.change_history_table == ChangeHistoryTable(
                table_name='"change-history-table-from-yaml"',
                schema_name="SCHEMACHANGE",
                database_name="METADATA",
            )
            assert config.config_vars == {"var1": "from_yaml", "var2": "also_from_yaml"}
            assert config.create_change_history_table is False
            assert config.autocommit is False
            assert config.dry_run is False
            assert config.query_tag == "query-tag-from-yaml"
            assert config.oauth_config == {
                "token-provider-url": "token-provider-url-from-yaml",
                "token-response-name": "token-response-name-from-yaml",
                "token-request-headers": {
                    "Content-Type": "Content-Type-from-yaml",
                    "User-Agent": "User-Agent-from-yaml",
                },
                "token-request-payload": {
                    "client_id": "id-from-yaml",
                    "username": "username-from-yaml",
                    "password": "password-from-yaml",
                    "grant_type": "type-from-yaml",
                    "scope": "scope-from-yaml",
                },
            }

    @mock.patch("pathlib.Path.is_dir", return_value=True)
    def test_all_cli_args(self, _):
        with mock.patch(
            "sys.argv",
            [
                "schemachange",
                "--config-folder",
                str(Path(__file__).parent),
                "--root-folder",
                "root-folder-from-cli",
                "--modules-folder",
                "modules-folder-from-cli",
                "--vars",
                '{"var1": "from_cli", "var3": "also_from_cli"}',
                "--snowflake-account",
                "snowflake-account-from-cli",
                "--snowflake-user",
                "snowflake-user-from-cli",
                "--snowflake-role",
                "snowflake-role-from-cli",
                "--snowflake-warehouse",
                "snowflake-warehouse-from-cli",
                "--snowflake-database",
                "snowflake-database-from-cli",
                "--snowflake-schema",
                "snowflake-schema-from-cli",
                "--change-history-table",
                "change-history-table-from-cli",
                "--create-change-history-table",
                "--autocommit",
                "--dry-run",
                "--query-tag",
                "query-tag-from-cli",
                "--oauth-config",
                '{"token-provider-url": "https//...", "token-request-payload": {"client_id": "GUID_xyz"} }',
                "--version_number_validation_regex",
                "version_number_validation_regex-from-cli",
                "--raise-exception-on-ignored-versioned-script",
            ],
        ):
            config = get_merged_config()

            assert config.snowflake_account == "snowflake-account-from-cli"
            assert config.snowflake_user == "snowflake-user-from-cli"
            assert config.snowflake_warehouse == '"snowflake-warehouse-from-cli"'
            assert config.snowflake_role == '"snowflake-role-from-cli"'
            assert str(config.root_folder) == "root-folder-from-cli"
            assert str(config.modules_folder) == "modules-folder-from-cli"
            assert config.snowflake_database == '"snowflake-database-from-cli"'
            assert config.snowflake_schema == '"snowflake-schema-from-cli"'
            assert config.change_history_table == ChangeHistoryTable(
                table_name='"change-history-table-from-cli"',
                schema_name="SCHEMACHANGE",
                database_name="METADATA",
            )
            assert config.config_vars == {
                "var1": "from_cli",
                "var2": "also_from_yaml",
                "var3": "also_from_cli",
            }
            assert config.create_change_history_table is True
            assert config.autocommit is True
            assert config.dry_run is True
            assert config.query_tag == "query-tag-from-cli"
            assert config.oauth_config == {
                "token-provider-url": "https//...",
                "token-request-payload": {"client_id": "GUID_xyz"},
            }
