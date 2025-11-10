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


def test_parse_args_deprecated_aliases_work():
    """Test that deprecated aliases still work (backward compatibility)"""
    # Test --vars deprecated alias
    args = ["deploy", "--vars", json.dumps({"var1": "value1"})]
    parsed_args = parse_cli_args(args)
    assert parsed_args["config_vars"] == {"var1": "value1"}

    # Test --query-tag deprecated alias
    args = ["deploy", "--query-tag", "my_tag"]
    parsed_args = parse_cli_args(args)
    assert parsed_args["query_tag"] == "my_tag"

    # Test --connection-name deprecated alias
    args = ["deploy", "--connection-name", "conn"]
    parsed_args = parse_cli_args(args)
    assert parsed_args["connection_name"] == "conn"

    # Test --root-folder deprecated alias
    args = ["deploy", "--root-folder", "some_folder"]
    parsed_args = parse_cli_args(args)
    assert parsed_args["root_folder"] == "some_folder"

    # Test --modules-folder deprecated alias
    args = ["deploy", "--modules-folder", "some_modules"]
    parsed_args = parse_cli_args(args)
    assert parsed_args["modules_folder"] == "some_modules"

    # Test --change-history-table deprecated alias
    args = ["deploy", "--change-history-table", "DB.SCHEMA.TABLE"]
    parsed_args = parse_cli_args(args)
    assert parsed_args["change_history_table"] == "DB.SCHEMA.TABLE"

    # Test --autocommit deprecated alias
    args = ["deploy", "--autocommit"]
    parsed_args = parse_cli_args(args)
    assert parsed_args["autocommit"] is True

    # Test --log-level deprecated alias
    args = ["deploy", "--log-level", "DEBUG"]
    parsed_args = parse_cli_args(args)
    assert parsed_args["log_level"] == logging.DEBUG


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
    """Test that authentication parameters can be passed via CLI arguments

    Note: --snowflake-private-key-passphrase is intentionally NOT supported via CLI
    for security reasons (would be visible in process list and shell history).
    Use SNOWFLAKE_PRIVATE_KEY_PASSPHRASE environment variable instead.
    """
    args = [
        "deploy",
        "--snowflake-authenticator",
        "snowflake_jwt",
        "--snowflake-private-key-path",
        "/path/to/key.pem",
        "--snowflake-token-file-path",
        "/path/to/token.txt",
    ]
    parsed_args = parse_cli_args(args)

    # Parser now uses snowflake_ prefix for all Snowflake connector params
    assert parsed_args["snowflake_authenticator"] == "snowflake_jwt"
    assert parsed_args["snowflake_private_key_path"] == "/path/to/key.pem"
    assert parsed_args["snowflake_token_file_path"] == "/path/to/token.txt"
    # private_key_passphrase should NOT be in parsed_args (CLI support removed for security)
    assert "snowflake_private_key_passphrase" not in parsed_args


def test_parse_args_private_key_passphrase_cli_not_supported():
    """Test that --snowflake-private-key-passphrase is NOT accepted via CLI

    This CLI argument was intentionally removed for security reasons.
    It should cause argparse to fail with "unrecognized arguments".
    """
    import pytest

    args = [
        "deploy",
        "--snowflake-private-key-passphrase",
        "my_passphrase",
    ]

    # Should raise SystemExit (argparse error for unrecognized argument)
    with pytest.raises(SystemExit):
        parse_cli_args(args)


def test_parse_args_all_argument_variants():
    """Test that all variants of consolidated arguments work correctly"""
    # Test config-folder variants
    for arg in ["--config-folder", "--schemachange-config-folder"]:
        args = ["deploy", arg, "test_folder"]
        parsed_args = parse_cli_args(args)
        assert parsed_args["config_folder"] == "test_folder"

    # Test config-file-name variants
    for arg in ["--config-file-name", "--schemachange-config-file-name"]:
        args = ["deploy", arg, "test_config.yml"]
        parsed_args = parse_cli_args(args)
        assert parsed_args["config_file_name"] == "test_config.yml"

    # Test root-folder variants
    for arg in ["-f", "--schemachange-root-folder", "--root-folder"]:
        args = ["deploy", arg, "test_root"]
        parsed_args = parse_cli_args(args)
        assert parsed_args["root_folder"] == "test_root"

    # Test modules-folder variants
    for arg in ["-m", "--schemachange-modules-folder", "--modules-folder"]:
        args = ["deploy", arg, "test_modules"]
        parsed_args = parse_cli_args(args)
        assert parsed_args["modules_folder"] == "test_modules"

    # Test vars variants
    test_vars = {"key": "value"}
    for arg in ["-V", "--schemachange-vars", "--vars"]:
        args = ["deploy", arg, json.dumps(test_vars)]
        parsed_args = parse_cli_args(args)
        assert parsed_args["config_vars"] == test_vars

    # Test log-level variants
    for arg in ["-L", "--schemachange-log-level", "--log-level"]:
        args = ["deploy", arg, "DEBUG"]
        parsed_args = parse_cli_args(args)
        assert parsed_args["log_level"] == logging.DEBUG

    # Test change-history-table variants
    for arg in ["-c", "--schemachange-change-history-table", "--change-history-table"]:
        args = ["deploy", arg, "TEST.TABLE"]
        parsed_args = parse_cli_args(args)
        assert parsed_args["change_history_table"] == "TEST.TABLE"

    # Test autocommit variants
    for arg in ["-ac", "--schemachange-autocommit", "--autocommit"]:
        args = ["deploy", arg]
        parsed_args = parse_cli_args(args)
        assert parsed_args["autocommit"] is True

    # Test query-tag variants
    for arg in ["-Q", "--schemachange-query-tag", "--query-tag"]:
        args = ["deploy", arg, "test_tag"]
        parsed_args = parse_cli_args(args)
        assert parsed_args["query_tag"] == "test_tag"

    # Test connection-name variants
    for arg in ["-C", "--schemachange-connection-name", "--connection-name"]:
        args = ["deploy", arg, "test_connection"]
        parsed_args = parse_cli_args(args)
        assert parsed_args["connection_name"] == "test_connection"

    # Test connections-file-path variants
    for arg in ["--schemachange-connections-file-path", "--connections-file-path"]:
        args = ["deploy", arg, "test_path.toml"]
        parsed_args = parse_cli_args(args)
        assert parsed_args["connections_file_path"] == "test_path.toml"

    # Test dry-run variants
    for arg in ["--schemachange-dry-run", "--dry-run"]:
        args = ["deploy", arg]
        parsed_args = parse_cli_args(args)
        assert parsed_args["dry_run"] is True

    # Test create-change-history-table variants
    for arg in ["--schemachange-create-change-history-table", "--create-change-history-table"]:
        args = ["deploy", arg]
        parsed_args = parse_cli_args(args)
        assert parsed_args["create_change_history_table"] is True


def test_parse_args_mixing_old_and_new_forms():
    """Test that mixing old and new forms works (last one wins)"""
    # Old form followed by new form - new form should win
    args = ["deploy", "--root-folder", "old_value", "-f", "new_value"]
    parsed_args = parse_cli_args(args)
    assert parsed_args["root_folder"] == "new_value"

    # New form followed by old form - old form should win (last specified)
    args = ["deploy", "-f", "new_value", "--root-folder", "old_value"]
    parsed_args = parse_cli_args(args)
    assert parsed_args["root_folder"] == "old_value"

    # Multiple variants - last one wins
    args = ["deploy", "--vars", '{"a":"1"}', "-V", '{"b":"2"}', "--schemachange-vars", '{"c":"3"}']
    parsed_args = parse_cli_args(args)
    assert parsed_args["config_vars"] == {"c": "3"}
