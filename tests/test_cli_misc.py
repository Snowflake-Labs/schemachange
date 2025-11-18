from dataclasses import asdict

import pytest

from schemachange.cli import SCHEMACHANGE_VERSION, SNOWFLAKE_APPLICATION_NAME
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import get_snowflake_identifier_string
from schemachange.deploy import alphanum_convert, get_alphanum_key, sorted_alphanumeric


def test_cli_given__schemachange_version_change_updated_in_setup_config_file():
    assert SCHEMACHANGE_VERSION == "4.2.0"


def test_cli_given__constants_exist():
    assert ChangeHistoryTable._default_database_name == "METADATA"
    assert ChangeHistoryTable._default_schema_name == "SCHEMACHANGE"
    assert ChangeHistoryTable._default_table_name == "CHANGE_HISTORY"
    assert SNOWFLAKE_APPLICATION_NAME == "schemachange"


def test_alphanum_convert_given__integer():
    assert alphanum_convert("123") == 123


def test_alphanum_convert_given__lowercase():
    assert alphanum_convert("TEST") == "test"


def test_get_alphanum_key_given__empty_string():
    assert get_alphanum_key("") == []


def test_get_alphanum_key_given__none():
    assert get_alphanum_key(None) == []


def test_get_alphanum_key_given__numbers_only():
    assert get_alphanum_key("123") == ["", 123, ""]


def test_get_alphanum_key_given__alphabets_only():
    assert get_alphanum_key("abc") == ["abc"]


def test_get_alphanum_key_given__upper_alphanumeric():
    assert get_alphanum_key("V1.2.3__") == [
        "v",
        1,
        ".",
        2,
        ".",
        3,
        "__",
    ]


def test_get_alphanum_key_given__valid_version_string():
    assert get_alphanum_key("1.2.2") == ["", 1, ".", 2, ".", 2, ""]


def test_sorted_alphanumeric_mixed_string():
    assert sorted_alphanumeric(["V1.2.3__file.sql", "V1.2.4__file.sql"]) == [
        "V1.2.3__file.sql",
        "V1.2.4__file.sql",
    ]


@pytest.mark.parametrize(
    "cht, expected",
    [
        (
            None,
            {
                "database_name": ChangeHistoryTable._default_database_name,
                "schema_name": ChangeHistoryTable._default_schema_name,
                "table_name": ChangeHistoryTable._default_table_name,
            },
        ),
        (
            "change_history_table",
            {
                "database_name": ChangeHistoryTable._default_database_name,
                "schema_name": ChangeHistoryTable._default_schema_name,
                "table_name": "change_history_table",
            },
        ),
        (
            "myschema.change_history_table",
            {
                "database_name": ChangeHistoryTable._default_database_name,
                "schema_name": "myschema",
                "table_name": "change_history_table",
            },
        ),
        (
            "mydb.myschema.change_history_table",
            {
                "database_name": "mydb",
                "schema_name": "myschema",
                "table_name": "change_history_table",
            },
        ),
        (
            '"change-history-table"',
            {
                "database_name": ChangeHistoryTable._default_database_name,
                "schema_name": ChangeHistoryTable._default_schema_name,
                "table_name": '"change-history-table"',
            },
        ),
        (
            '"my-schema"."change-history-table"',
            {
                "database_name": ChangeHistoryTable._default_database_name,
                "schema_name": '"my-schema"',
                "table_name": '"change-history-table"',
            },
        ),
        (
            '"my-db"."my-schema"."change-history-table"',
            {
                "database_name": '"my-db"',
                "schema_name": '"my-schema"',
                "table_name": '"change-history-table"',
            },
        ),
    ],
)
def test_get_change_history_table_details_given__acceptable_values_produces_fully_qualified_change_history_table_name(
    cht, expected
):
    assert asdict(ChangeHistoryTable.from_str(cht)) == expected


@pytest.mark.parametrize("cht", ["fifth.fourth.third.two.one", "fourth.third.two.one"])
def test_get_change_history_table_details_given__unacceptable_values_raises_error(cht):
    with pytest.raises(ValueError) as e:
        ChangeHistoryTable.from_str(cht)

    assert str(e.value).startswith("Invalid change history table name: ")


@pytest.mark.parametrize(
    "input_value, input_type, expected_value",
    [
        (None, "role", None),
        ("valid_value_123", "role", "valid_value_123"),
        ("valid-value-123", "role", '"valid-value-123"'),
        ('"valid-value-123"', "role", '"valid-value-123"'),
    ],
)
def test__get_snowflake_identifier_string_given__acceptable_values_produces_properly_quoted_snowflake_identifier(
    input_value, input_type, expected_value
):
    assert get_snowflake_identifier_string(input_value, input_type) == expected_value


@pytest.mark.parametrize(
    "input_value, input_type",
    [('"valid-value-123', "role"), ('valid-value-123"', "role")],
)
def test__get_snowflake_identifier_string_given__unacceptable_values_raises_error(input_value, input_type):
    with pytest.raises(ValueError) as e:
        get_snowflake_identifier_string(input_value, input_type)

    assert str(e.value).startswith(f"Invalid {input_type}: ")
