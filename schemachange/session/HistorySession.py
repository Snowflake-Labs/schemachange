from __future__ import annotations

from collections import defaultdict
from textwrap import dedent, indent

import snowflake.connector
import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import get_snowflake_identifier_string


class HistorySession:
    """Dedicated session for change history table operations."""

    def __init__(
        self,
        schemachange_version: str,
        application: str,
        change_history_table: ChangeHistoryTable,
        logger: structlog.BoundLogger,
        connection_name: str | None = None,
        connections_file_path: str | None = None,
        account: str | None = None,
        user: str | None = None,
        role: str | None = None,
        warehouse: str | None = None,
        database: str | None = None,
        schema: str | None = None,
        query_tag: str | None = None,
        autocommit: bool = False,
        **kwargs,
    ):
        self.change_history_table = change_history_table
        self.autocommit = autocommit
        self.logger = logger

        self.session_parameters = {
            "QUERY_TAG": f"schemachange_history {schemachange_version}"
        }
        if query_tag:
            self.session_parameters["QUERY_TAG"] += f";{query_tag}"

        connect_kwargs = {
            "account": account,
            "user": user,
            "database": database,
            "schema": schema,
            "role": role,
            "warehouse": warehouse,
            "private_key_file": kwargs.get("private_key_path"),
            "token": kwargs.get("oauth_token"),
            "password": kwargs.get("password"),
            "authenticator": kwargs.get("authenticator"),
            "connection_name": connection_name,
            "connections_file_path": connections_file_path,
            "application": application,
            "session_parameters": self.session_parameters,
        }
        connect_kwargs = {k: v for k, v in connect_kwargs.items() if v is not None}
        self.logger.debug("snowflake.connector.connect kwargs", **connect_kwargs)
        self.con = snowflake.connector.connect(**connect_kwargs)

        self.account = self.con.account
        self.user = get_snowflake_identifier_string(self.con.user, "user")
        self.role = get_snowflake_identifier_string(self.con.role, "role")
        self.warehouse = get_snowflake_identifier_string(
            self.con.warehouse, "warehouse"
        )
        self.database = get_snowflake_identifier_string(self.con.database, "database")
        self.schema = get_snowflake_identifier_string(self.con.schema, "schema")

        if not self.autocommit:
            self.con.autocommit(False)

    def __del__(self):
        if hasattr(self, "con"):
            self.con.close()

    def execute_query(self, query: str, logger: structlog.BoundLogger):
        """Execute a single SQL query using the simplest Snowflake connector method."""
        logger.debug(
            "Executing history query",
            query=indent(query, prefix="\t"),
        )
        try:
            cursor = self.con.cursor()
            cursor.execute(query)

            if not self.autocommit:
                self.con.commit()
            return cursor
        except Exception as e:
            if not self.autocommit:
                self.con.rollback()
            raise e

    def fetch_change_history_metadata(self) -> dict:
        """Fetch metadata about the change history table."""
        query = f"""\
            SELECT
                CREATED,
                LAST_ALTERED
            FROM {self.change_history_table.database_name}.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = REPLACE('{self.change_history_table.schema_name}','\"','')
                AND TABLE_NAME = REPLACE('{self.change_history_table.table_name}','\"','')
        """
        cursor = self.execute_query(query=dedent(query), logger=self.logger)

        change_history_metadata = dict()
        for row in cursor:
            change_history_metadata["created"] = row[0]
            change_history_metadata["last_altered"] = row[1]

        return change_history_metadata

    def change_history_schema_exists(self) -> bool:
        """Check if the change history schema exists."""
        query = f"""\
            SELECT
                COUNT(1)
            FROM {self.change_history_table.database_name}.INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME = REPLACE('{self.change_history_table.schema_name}','\"','')
        """
        cursor = self.execute_query(dedent(query), logger=self.logger)
        for row in cursor:
            return row[0] > 0

    def create_change_history_schema(self, dry_run: bool) -> None:
        """Create the change history schema."""
        query = f"CREATE SCHEMA IF NOT EXISTS {self.change_history_table.fully_qualified_schema_name}"
        if dry_run:
            self.logger.debug(
                "Running in dry-run mode. Skipping execution.",
                query=indent(dedent(query), prefix="\t"),
            )
        else:
            self.execute_query(dedent(query), logger=self.logger)

    def create_change_history_table(self, dry_run: bool) -> None:
        """Create the change history table."""
        query = f"""\
            CREATE TABLE IF NOT EXISTS {self.change_history_table.fully_qualified} (
                VERSION VARCHAR,
                DESCRIPTION VARCHAR,
                SCRIPT VARCHAR,
                SCRIPT_TYPE VARCHAR,
                CHECKSUM VARCHAR,
                EXECUTION_TIME NUMBER,
                STATUS VARCHAR,
                INSTALLED_BY VARCHAR,
                INSTALLED_ON TIMESTAMP_LTZ
            )
        """
        if dry_run:
            self.logger.debug(
                "Running in dry-run mode. Skipping execution.",
                query=indent(dedent(query), prefix="\t"),
            )
        else:
            self.execute_query(dedent(query), logger=self.logger)
            self.logger.info(
                f"Created change history table {self.change_history_table.fully_qualified}"
            )

    def change_history_table_exists(
        self, create_change_history_table: bool, dry_run: bool
    ) -> bool:
        """Check if change history table exists, create if needed."""
        change_history_metadata = self.fetch_change_history_metadata()
        if change_history_metadata:
            self.logger.info(
                f"Using existing change history table {self.change_history_table.fully_qualified}",
                last_altered=change_history_metadata["last_altered"],
            )
            return True
        elif create_change_history_table:
            schema_exists = self.change_history_schema_exists()
            if not schema_exists:
                self.create_change_history_schema(dry_run=dry_run)
            self.create_change_history_table(dry_run=dry_run)
            if dry_run:
                return False
            self.logger.info("Created change history table")
            return True
        else:
            raise ValueError(
                f"Unable to find change history table {self.change_history_table.fully_qualified}"
            )

    def fetch_repeatable_scripts(self) -> dict[str, list[str]]:
        """Fetch repeatable script checksums."""
        query = f"""\
        SELECT DISTINCT
            SCRIPT AS SCRIPT_NAME,
            FIRST_VALUE(CHECKSUM) OVER (
                PARTITION BY SCRIPT
                ORDER BY INSTALLED_ON DESC
            ) AS CHECKSUM
        FROM {self.change_history_table.fully_qualified}
        WHERE SCRIPT_TYPE = 'R'
            AND STATUS = 'Success'
        """
        cursor = self.execute_query(dedent(query), logger=self.logger)

        script_checksums: dict[str, list[str]] = defaultdict(list)
        for script_name, checksum in cursor:
            script_checksums[script_name].append(checksum)
        return script_checksums

    def fetch_versioned_scripts(
        self,
    ) -> tuple[dict[str, dict[str, str | int]], str | int | None]:
        """Fetch versioned script history."""
        query = f"""\
        SELECT VERSION, SCRIPT, CHECKSUM
        FROM {self.change_history_table.fully_qualified}
        WHERE SCRIPT_TYPE = 'V'
        ORDER BY INSTALLED_ON DESC
        """
        cursor = self.execute_query(dedent(query), logger=self.logger)

        versioned_scripts: dict[str, dict[str, str | int]] = defaultdict(dict)
        versions: list[str | int | None] = []
        for version, script, checksum in cursor:
            versions.append(version if version != "" else None)
            versioned_scripts[script] = {
                "version": version,
                "script": script,
                "checksum": checksum,
            }

        return versioned_scripts, versions[0] if versions else None

    def insert_change_record(
        self,
        version: str,
        description: str,
        script_name: str,
        script_type: str,
        checksum: str,
        execution_time: int,
        status: str,
        installed_by: str,
        logger: structlog.BoundLogger,
    ) -> None:
        """Insert a record into the change history table."""
        query = f"""\
            INSERT INTO {self.change_history_table.fully_qualified} (
                VERSION,
                DESCRIPTION,
                SCRIPT,
                SCRIPT_TYPE,
                CHECKSUM,
                EXECUTION_TIME,
                STATUS,
                INSTALLED_BY,
                INSTALLED_ON
            ) VALUES (
                '{version}',
                '{description}',
                '{script_name}',
                '{script_type}',
                '{checksum}',
                {execution_time},
                '{status}',
                '{installed_by}',
                CURRENT_TIMESTAMP
            );
        """
        self.execute_query(dedent(query), logger=logger)
