from __future__ import annotations

import json

from schemachange.config.parse_cli_args import parse_cli_args


def test_parse_args_defaults():
    args: list[str] = []
    test_args = [
        ("--config-folder", None, "."),
        ("--config-file-name", None, "schemachange-config.yml"),
        ("--config-vars", None, {}),
    ]
    expected: dict[str, str | int | None] = {}
    for arg, value, expected_value in test_args:
        if value:
            args.extend([arg, value])
        expected_arg = arg.strip("-").replace("-", "_")
        expected[expected_arg] = expected_value

    parsed_args = parse_cli_args(args)
    for expected_arg, expected_value in expected.items():
        assert parsed_args[expected_arg] == expected_value
    assert parsed_args["subcommand"] == "deploy"


def test_parse_args_deploy_names():
    args: list[str] = ["deploy"]
    expected: dict[str, str | int] = {}

    valued_test_args: list[tuple[str, str, str]] = [
        ("--config-folder", "some_config_folder_name", "some_config_folder_name"),
        ("--config-file-name", "some_config_file_name", "some_config_file_name"),
        ("--root-folder", "some_root_folder_name", "some_root_folder_name"),
        ("--modules-folder", "some_modules_folder_name", "some_modules_folder_name"),
        ("--vars", json.dumps({"some": "vars"}), {"some": "vars"}),
        ("--snowflake-account", "some_snowflake_account", "some_snowflake_account"),
        ("--snowflake-user", "some_snowflake_user", "some_snowflake_user"),
        ("--snowflake-role", "some_snowflake_role", "some_snowflake_role"),
        (
            "--snowflake-warehouse",
            "some_snowflake_warehouse",
            "some_snowflake_warehouse",
        ),
        ("--snowflake-database", "some_snowflake_database", "some_snowflake_database"),
        ("--snowflake-schema", "some_snowflake_schema", "some_snowflake_schema"),
        (
            "--snowflake-authenticator",
            "some_snowflake_authenticator",
            "some_snowflake_authenticator",
        ),
        (
            "--snowflake-private-key-path",
            "some_snowflake_private_key_path",
            "some_snowflake_private_key_path",
        ),
        (
            "--snowflake-token-path",
            "some_snowflake_token_path",
            "some_snowflake_token_path",
        ),
        (
            "--connections-file-path",
            "some_connections_file_path",
            "some_connections_file_path",
        ),
        ("--connection-name", "some_connection_name", "some_connection_name"),
        ("--change-history-table", "some_history_table", "some_history_table"),
        ("--query-tag", "some_query_tag", "some_query_tag"),
    ]

    for arg, value, expected_value in valued_test_args:
        if value:
            args.extend([arg, value])
        expected_arg = arg.strip("-").replace("-", "_")
        expected[expected_arg] = expected_value

    valueless_test_args: list[tuple[str, bool]] = [
        ("--create-change-history-table", True),
        ("--autocommit", True),
        ("--dry-run", True),
    ]

    for arg, expected_value in valueless_test_args:
        args.extend([arg])
        expected_arg = arg.strip("-").replace("-", "_")
        expected[expected_arg] = expected_value

    parsed_args = parse_cli_args(args)
    assert parsed_args["subcommand"] == "deploy"
    for expected_arg, expected_value in expected.items():
        if expected_arg == "vars":
            expected_arg = "config_vars"
        assert parsed_args[expected_arg] == expected_value


def test_parse_args_deploy_flags():
    args: list[str] = ["deploy"]
    expected: dict[str, str | int] = {}

    valued_test_args: list[tuple[str, str, str, str]] = [
        ("-f", "root_folder", "some_root_folder_name", "some_root_folder_name"),
        (
            "-m",
            "modules_folder",
            "some_modules_folder_name",
            "some_modules_folder_name",
        ),
        ("-a", "snowflake_account", "some_snowflake_account", "some_snowflake_account"),
        ("-u", "snowflake_user", "some_snowflake_user", "some_snowflake_user"),
        ("-r", "snowflake_role", "some_snowflake_role", "some_snowflake_role"),
        (
            "-w",
            "snowflake_warehouse",
            "some_snowflake_warehouse",
            "some_snowflake_warehouse",
        ),
        (
            "-d",
            "snowflake_database",
            "some_snowflake_database",
            "some_snowflake_database",
        ),
        ("-s", "snowflake_schema", "some_snowflake_schema", "some_snowflake_schema"),
        (
            "-A",
            "snowflake_authenticator",
            "some_snowflake_authenticator",
            "some_snowflake_authenticator",
        ),
        (
            "-k",
            "snowflake_private_key_path",
            "some_snowflake_private_key_path",
            "some_snowflake_private_key_path",
        ),
        (
            "-t",
            "snowflake_token_path",
            "some_snowflake_token_path",
            "some_snowflake_token_path",
        ),
        ("-c", "change_history_table", "some_history_table", "some_history_table"),
    ]

    for arg, expected_arg, value, expected_value in valued_test_args:
        if value:
            args.extend([arg, value])
        expected[expected_arg] = expected_value

    valueless_test_args: list[tuple[str, str, bool]] = [
        ("-ac", "autocommit", True),
    ]

    for arg, expected_arg, expected_value in valueless_test_args:
        args.extend([arg])
        expected[expected_arg] = expected_value

    parsed_args = parse_cli_args(args)
    assert parsed_args["subcommand"] == "deploy"
    for expected_arg, expected_value in expected.items():
        assert parsed_args[expected_arg] == expected_value
