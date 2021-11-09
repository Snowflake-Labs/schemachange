import pytest
from schemachange.cli import (
    get_change_history_table_details, 
    _metadata_database_name, 
    _metadata_schema_name, 
    _metadata_table_name,
)

@pytest.mark.parametrize(
    "config, expected_details",
    [
        (
            {
                "change-history-table": None, 
                "change-history-table-use-default-db-conn": False,
            },
            {
                "database_name": _metadata_database_name.upper(),
                "schema_name": _metadata_schema_name.upper(),
                "table_name": _metadata_table_name.upper(),
            }
        ),
        (
            {
                "change-history-table": "table_name", 
                "change-history-table-use-default-db-conn": False,
            },
            {
                "database_name": _metadata_database_name.upper(),
                "schema_name": _metadata_schema_name.upper(),
                "table_name": "TABLE_NAME",
            }
        ),
        (
            {
                "change-history-table": "test_schema.table_name", 
                "change-history-table-use-default-db-conn": False,
            },
            {
                "database_name": _metadata_database_name.upper(),
                "schema_name": "TEST_SCHEMA",
                "table_name": "TABLE_NAME",
            }
        ),
        (
            {
                "change-history-table": "test_db.test_schema.table_name", 
                "change-history-table-use-default-db-conn": False,
            },
            {
                "database_name": "TEST_DB",
                "schema_name": "TEST_SCHEMA",
                "table_name": "TABLE_NAME",
            }
        ),

    ]
)
def test_get_change_history_table_details_backward_compatibility(config, expected_details):
    assert expected_details == get_change_history_table_details(config)


@pytest.mark.parametrize(
    "config, expected_details",
    [
        (
            {
                "change-history-table": None, 
                "change-history-table-use-default-db-conn": True,
                "snowflake-database": "test_db",
                "snowflake-schema": "test_schema",
            },
            {
                "database_name": "TEST_DB",
                "schema_name": "TEST_SCHEMA",
                "table_name": _metadata_table_name.upper(),
            }
        ),
        (
            {
                "change-history-table": None, 
                "change-history-table-use-default-db-conn": True,
                "snowflake-database": "test_db",
            },
            {
                "database_name": "TEST_DB",
                "schema_name": _metadata_schema_name.upper(),
                "table_name": _metadata_table_name.upper(),
            }
        ),
        (
            {
                "change-history-table": None, 
                "change-history-table-use-default-db-conn": True,
            },
            {
                "database_name": _metadata_database_name.upper(),
                "schema_name": _metadata_schema_name.upper(),
                "table_name": _metadata_table_name.upper(),
            }
        ),
        (
            {
                "change-history-table": "table_name", 
                "change-history-table-use-default-db-conn": True,
                "snowflake-database": "test_db",
                "snowflake-schema": "test_schema",
            },
            {
                "database_name": "TEST_DB",
                "schema_name": "TEST_SCHEMA",
                "table_name": "TABLE_NAME",
            }
        ),
    ]
)
def test_get_change_history_table_details_use_default_db_conn(config, expected_details):
    assert expected_details == get_change_history_table_details(config)
