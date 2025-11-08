from __future__ import annotations

import json
import logging

import pytest

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
    assert parsed_args.get("raise_exception_on_ignored_versioned_script") is None
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
            "--connections-file-path",
            "some_connections_file_path",
            "some_connections_file_path",
        ),
        ("--connection-name", "some_connection_name", "some_connection_name"),
        ("--change-history-table", "some_history_table", "some_history_table"),
        ("--query-tag", "some_query_tag", "some_query_tag"),
        ("--version-number-validation-regex", "some_regex", "some_regex"),
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
        ("--raise-exception-on-ignored-versioned-script", True),
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


def test_parse_args_verbose_deprecation():
    args: list[str] = ["--verbose"]
    with pytest.warns(UserWarning) as warning:
        parsed_args = parse_cli_args(args)
    assert parsed_args.get("verbose", None) is None
    assert parsed_args["log_level"] is logging.DEBUG
    assert (
        str(warning[0].message)
        == "Argument ['-v', '--verbose'] is deprecated and will be interpreted as a DEBUG log level."
    )


def test_parse_args_new_prefixed_long_forms():
    """Test new --schemachange-* prefixed arguments work correctly"""
    args: list[str] = ["deploy"]
    expected: dict[str, str | int] = {}

    valued_test_args: list[tuple[str, str, str]] = [
        ("--schemachange-root-folder", "some_root_folder", "some_root_folder"),
        ("--schemachange-modules-folder", "some_modules_folder", "some_modules_folder"),
        ("--schemachange-vars", json.dumps({"var1": "value1"}), {"var1": "value1"}),
        ("--schemachange-query-tag", "some_query_tag", "some_query_tag"),
        ("--schemachange-connection-name", "some_connection", "some_connection"),
        ("--schemachange-connections-file-path", "some/path.toml", "some/path.toml"),
        ("--schemachange-change-history-table", "SCHEMA.TABLE", "SCHEMA.TABLE"),
        ("--schemachange-version-number-validation-regex", "^[0-9]+$", "^[0-9]+$"),
    ]

    for arg, value, expected_value in valued_test_args:
        args.extend([arg, value])
        expected_arg = arg.replace("--schemachange-", "").replace("-", "_")
        if expected_arg == "vars":
            expected_arg = "config_vars"
        expected[expected_arg] = expected_value

    valueless_test_args: list[tuple[str, bool]] = [
        ("--schemachange-create-change-history-table", True),
        ("--schemachange-autocommit", True),
        ("--schemachange-dry-run", True),
        ("--schemachange-raise-exception-on-ignored-versioned-script", True),
    ]

    for arg, expected_value in valueless_test_args:
        args.append(arg)
        expected_arg = arg.replace("--schemachange-", "").replace("-", "_")
        expected[expected_arg] = expected_value

    parsed_args = parse_cli_args(args)
    assert parsed_args["subcommand"] == "deploy"
    for expected_arg, expected_value in expected.items():
        assert parsed_args[expected_arg] == expected_value


def test_parse_args_new_capital_short_forms():
    """Test new capital letter short forms (-V, -L, -Q, -C) work correctly"""
    args: list[str] = ["deploy"]
    expected: dict[str, str | int] = {}

    valued_test_args: list[tuple[str, str, str, str]] = [
        ("-V", "config_vars", json.dumps({"var1": "value1"}), {"var1": "value1"}),
        ("-L", "log_level", "DEBUG", logging.DEBUG),
        ("-Q", "query_tag", "my_tag", "my_tag"),
        ("-C", "connection_name", "my_connection", "my_connection"),
    ]

    for arg, expected_arg, value, expected_value in valued_test_args:
        args.extend([arg, value])
        expected[expected_arg] = expected_value

    parsed_args = parse_cli_args(args)
    assert parsed_args["subcommand"] == "deploy"
    for expected_arg, expected_value in expected.items():
        assert parsed_args[expected_arg] == expected_value


def test_parse_args_lowercase_short_forms_no_deprecation():
    """Test lowercase short forms (-f, -m, -c, -ac) work without deprecation"""
    args: list[str] = ["deploy", "-f", "folder", "-m", "modules", "-c", "table", "-ac"]
    parsed_args = parse_cli_args(args)

    assert parsed_args["root_folder"] == "folder"
    assert parsed_args["modules_folder"] == "modules"
    assert parsed_args["change_history_table"] == "table"
    assert parsed_args["autocommit"] is True
    assert parsed_args["subcommand"] == "deploy"


def test_parse_args_snowflake_args_no_deprecation():
    """Test --snowflake-* arguments work without deprecation warnings"""
    args: list[str] = [
        "deploy",
        "-a",
        "account",
        "-u",
        "user",
        "-r",
        "role",
        "-w",
        "warehouse",
        "-d",
        "database",
        "-s",
        "schema",
    ]
    parsed_args = parse_cli_args(args)

    assert parsed_args["snowflake_account"] == "account"
    assert parsed_args["snowflake_user"] == "user"
    assert parsed_args["snowflake_role"] == "role"
    assert parsed_args["snowflake_warehouse"] == "warehouse"
    assert parsed_args["snowflake_database"] == "database"
    assert parsed_args["snowflake_schema"] == "schema"


def test_parse_args_old_unprefixed_show_deprecation(capsys):
    """Test old unprefixed arguments show deprecation warnings"""
    # Test --vars deprecation
    args = ["deploy", "--vars", json.dumps({"var1": "value1"})]
    parsed_args = parse_cli_args(args)
    captured = capsys.readouterr()
    assert "--vars is deprecated" in captured.err
    assert "-V or --schemachange-vars" in captured.err
    assert "SCHEMACHANGE_VARS" in captured.err
    assert parsed_args["config_vars"] == {"var1": "value1"}

    # Test --query-tag deprecation
    args = ["deploy", "--query-tag", "my_tag"]
    parsed_args = parse_cli_args(args)
    captured = capsys.readouterr()
    assert "--query-tag is deprecated" in captured.err
    assert "-Q or --schemachange-query-tag" in captured.err
    assert parsed_args["query_tag"] == "my_tag"

    # Test --connection-name deprecation
    args = ["deploy", "--connection-name", "conn"]
    parsed_args = parse_cli_args(args)
    captured = capsys.readouterr()
    assert "--connection-name is deprecated" in captured.err
    assert "-C or --schemachange-connection-name" in captured.err
    assert parsed_args["connection_name"] == "conn"


def test_parse_args_parameter_precedence():
    """Test that new prefixed arguments take precedence when both old and new specified"""
    # When both --vars and -V are specified, -V should win
    args = ["deploy", "--vars", json.dumps({"old": "value"}), "-V", json.dumps({"new": "value"})]
    parsed_args = parse_cli_args(args)
    # argparse will use the last one specified, which is the new one
    assert parsed_args["config_vars"] == {"new": "value"}

    # When both --query-tag and -Q are specified, -Q should win
    args = ["deploy", "--query-tag", "old_tag", "-Q", "new_tag"]
    parsed_args = parse_cli_args(args)
    assert parsed_args["query_tag"] == "new_tag"


def test_parse_args_authentication_parameters():
    """Test that authentication parameters can be passed via CLI arguments"""
    args = [
        "deploy",
        "--snowflake-authenticator",
        "snowflake_jwt",
        "--snowflake-private-key-path",
        "/path/to/key.pem",
        "--snowflake-private-key-passphrase",
        "my_passphrase",
        "--snowflake-token-file-path",
        "/path/to/token.txt",
    ]
    parsed_args = parse_cli_args(args)

    assert parsed_args["authenticator"] == "snowflake_jwt"
    assert parsed_args["private_key_path"] == "/path/to/key.pem"
    assert parsed_args["private_key_passphrase"] == "my_passphrase"
    assert parsed_args["token_file_path"] == "/path/to/token.txt"
