import json

from schemachange.parse_args import parse_args


def test_parse_args_defaults():
    args: list[str] = []
    test_args = [("--config-folder", None, ".")]
    expected: dict[str, str | int] = {}
    for arg, value, expected_value in test_args:
        if value:
            args.extend([arg, value])
        expected_arg = arg.strip("-").replace("-", "_")
        expected[expected_arg] = expected_value

    parsed_args = parse_args(args)
    for expected_arg, expected_value in expected.items():
        something = getattr(parsed_args, expected_arg)
        assert something == expected_value
    assert parsed_args.verbose is False
    assert parsed_args.create_change_history_table is False
    assert parsed_args.autocommit is False
    assert parsed_args.dry_run is False
    assert parsed_args.raise_exception_on_ignored_versioned_migration is False
    assert parsed_args.subcommand == "deploy"


def test_parse_args_deploy_names():
    args: list[str] = ["deploy"]
    expected: dict[str, str | int] = {}

    valued_test_args: list[tuple[str, str, str]] = [
        ("--config-folder", "some_config_folder_name", "some_config_folder_name"),
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
        ("--change-history-table", "some_history_table", "some_history_table"),
        ("--query-tag", "some_query_tag", "some_query_tag"),
        ("--oauth-config", json.dumps({"some": "values"}), {"some": "values"}),
        ("--version_number_validation_regex", "some_regex", "some_regex"),
    ]

    for arg, value, expected_value in valued_test_args:
        if value:
            args.extend([arg, value])
        expected_arg = arg.strip("-").replace("-", "_")
        expected[expected_arg] = expected_value

    valueless_test_args: list[tuple[str, bool]] = [
        ("--verbose", True),
        ("--create-change-history-table", True),
        ("--autocommit", True),
        ("--dry-run", True),
        ("--raise-exception-on-ignored-versioned-migration", True),
    ]

    for arg, expected_value in valueless_test_args:
        args.extend([arg])
        expected_arg = arg.strip("-").replace("-", "_")
        expected[expected_arg] = expected_value

    parsed_args = parse_args(args)
    for expected_arg, expected_value in expected.items():
        something = getattr(parsed_args, expected_arg)
        assert something == expected_value


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
        ("-v", "verbose", True),
        ("-ac", "autocommit", True),
    ]

    for arg, expected_arg, expected_value in valueless_test_args:
        args.extend([arg])
        expected[expected_arg] = expected_value

    parsed_args = parse_args(args)
    for expected_arg, expected_value in expected.items():
        something = getattr(parsed_args, expected_arg)
        assert something == expected_value
