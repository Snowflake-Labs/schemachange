from __future__ import annotations


import pytest

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable


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
def test_from_str_happy_path(table_str: str, expected: ChangeHistoryTable):
    result = ChangeHistoryTable.from_str(table_str)
    assert result == expected


def test_from_str_exception():
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
def test_fully_qualified(table: ChangeHistoryTable, expected: str):
    result = table.fully_qualified
    assert result == expected
