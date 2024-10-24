from __future__ import annotations

import hashlib
import time
from collections import defaultdict
from textwrap import dedent, indent

import snowflake.connector
import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.session.Script import VersionedScript, RepeatableScript, AlwaysScript


class SnowflakeSession:
    user: str | None
    role: str | None
    warehouse: str | None
    database: str | None
    schema: str | None
    autocommit: bool
    change_history_table: ChangeHistoryTable
    logger: structlog.BoundLogger
    session_parameters: dict[str, str]
    conn: snowflake.connector.SnowflakeConnection

    """
    Manages Snowflake Interactions and authentication
    """

    def __init__(
        self,
        schemachange_version: str,
        application: str,
        change_history_table: ChangeHistoryTable,
        logger: structlog.BoundLogger,
        user: str | None = None,
        role: str | None = None,
        warehouse: str | None = None,
        database: str | None = None,
        schema: str | None = None,
        query_tag: str | None = None,
        autocommit: bool = False,
        **kwargs,
    ):
        self.user = user
        self.role = role
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        self.change_history_table = change_history_table
        self.autocommit = autocommit
        self.logger = logger

        self.session_parameters = {"QUERY_TAG": f"schemachange {schemachange_version}"}
        if query_tag:
            self.session_parameters["QUERY_TAG"] += f";{query_tag}"

        self.con = snowflake.connector.connect(
            account=kwargs["account"],
            user=self.user,
            database=kwargs.get("database"),
            schema=kwargs.get("schema"),
            role=self.role,
            warehouse=self.warehouse,
            private_key=kwargs.get("private_key"),
            private_key_file=kwargs.get("private_key_path"),
            private_key_file_pwd=kwargs.get("private_key_path_password"),
            token=kwargs.get("oauth_token"),
            password=kwargs.get("password"),
            authenticator=kwargs.get("authenticator"),
            connection_name=kwargs.get("connection_name"),
            connections_file_path=kwargs.get("connections_file_path"),
            application=application,
            session_parameters=self.session_parameters,
        )
        print(f"Current session ID: {self.con.session_id}")

        if not self.autocommit:
            self.con.autocommit(False)

    def __del__(self):
        if hasattr(self, "con"):
            self.con.close()

    def execute_snowflake_query(self, query: str, logger: structlog.BoundLogger):
        logger.debug(
            "Executing query",
            query=indent(query, prefix="\t"),
        )
        try:
            res = self.con.execute_string(query)
            if not self.autocommit:
                self.con.commit()
            return res
        except Exception as e:
            if not self.autocommit:
                self.con.rollback()
            raise e

    def fetch_change_history_metadata(self) -> dict:
        # This should only ever return 0 or 1 rows
        query = f"""\
            SELECT
                CREATED,
                LAST_ALTERED
            FROM {self.change_history_table.database_name}.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = REPLACE('{self.change_history_table.schema_name}','\"','')
                AND TABLE_NAME = REPLACE('{self.change_history_table.table_name}','\"','')
        """
        results = self.execute_snowflake_query(query=dedent(query), logger=self.logger)

        # Collect all the results into a list
        change_history_metadata = dict()
        for cursor in results:
            for row in cursor:
                change_history_metadata["created"] = row[0]
                change_history_metadata["last_altered"] = row[1]

        return change_history_metadata

    def change_history_schema_exists(self) -> bool:
        query = f"""\
            SELECT
                COUNT(1)
            FROM {self.change_history_table.database_name}.INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME = REPLACE('{self.change_history_table.schema_name}','\"','')
        """
        results = self.execute_snowflake_query(dedent(query), logger=self.logger)
        for cursor in results:
            for row in cursor:
                return row[0] > 0

    def create_change_history_schema(self, dry_run: bool) -> None:
        query = f"CREATE SCHEMA IF NOT EXISTS {self.change_history_table.schema_name}"
        if dry_run:
            self.logger.debug(
                "Running in dry-run mode. Skipping execution.",
                query=indent(dedent(query), prefix="\t"),
            )
        else:
            self.execute_snowflake_query(dedent(query), logger=self.logger)

    def create_change_history_table(self, dry_run: bool) -> None:
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
            self.execute_snowflake_query(dedent(query), logger=self.logger)
            self.logger.info(
                f"Created change history table {self.change_history_table.fully_qualified}"
            )

    def change_history_table_exists(
        self, create_change_history_table: bool, dry_run: bool
    ) -> bool:
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

    def get_script_metadata(
        self, create_change_history_table: bool, dry_run: bool
    ) -> tuple[
        dict[str, dict[str, str | int]] | None,
        dict[str, list[str]] | None,
        str | int | None,
    ]:
        change_history_table_exists = self.change_history_table_exists(
            create_change_history_table=create_change_history_table,
            dry_run=dry_run,
        )
        if not change_history_table_exists:
            return None, None, None

        change_history, max_published_version = self.fetch_versioned_scripts()
        r_scripts_checksum = self.fetch_repeatable_scripts()

        self.logger.info(
            "Max applied change script version %(max_published_version)s"
            % {
                "max_published_version": (
                    max_published_version if max_published_version != "" else "None"
                )
            }
        )
        return change_history, r_scripts_checksum, max_published_version

    def fetch_repeatable_scripts(self) -> dict[str, list[str]]:
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
        results = self.execute_snowflake_query(dedent(query), logger=self.logger)

        # Collect all the results into a dict
        script_checksums: dict[str, list[str]] = defaultdict(list)
        for cursor in results:
            for script_name, checksum in cursor:
                script_checksums[script_name].append(checksum)
        return script_checksums

    def fetch_versioned_scripts(
        self,
    ) -> tuple[dict[str, dict[str, str | int]], str | int | None]:
        query = f"""\
        SELECT VERSION, SCRIPT, CHECKSUM
        FROM {self.change_history_table.fully_qualified}
        WHERE SCRIPT_TYPE = 'V'
        ORDER BY INSTALLED_ON DESC -- TODO: Why not order by version?
        """
        results = self.execute_snowflake_query(dedent(query), logger=self.logger)

        # Collect all the results into a list
        versioned_scripts: dict[str, dict[str, str | int]] = defaultdict(dict)
        versions: list[str | int] = []
        for cursor in results:
            for version, script, checksum in cursor:
                versions.append(version)
                versioned_scripts[script] = {
                    "version": version,
                    "script": script,
                    "checksum": checksum,
                }

        # noinspection PyTypeChecker
        return versioned_scripts, versions[0] if versions else None

    def reset_session(self, logger: structlog.BoundLogger):
        # These items are optional, so we can only reset the ones with values
        reset_query = []
        if self.role:
            reset_query.append(f"USE ROLE IDENTIFIER('{self.role}');")
        if self.warehouse:
            reset_query.append(f"USE WAREHOUSE IDENTIFIER('{self.warehouse}');")
        if self.database:
            reset_query.append(f"USE DATABASE IDENTIFIER('{self.database}');")
        if self.schema:
            reset_query.append(f"USE SCHEMA IDENTIFIER('{self.schema}');")

        self.execute_snowflake_query("\n".join(reset_query), logger=logger)

    def reset_query_tag(self, logger: structlog.BoundLogger, extra_tag=None):
        query_tag = self.session_parameters["QUERY_TAG"]
        if extra_tag:
            query_tag += f";{extra_tag}"

        self.execute_snowflake_query(
            f"ALTER SESSION SET QUERY_TAG = '{query_tag}'", logger=logger
        )

    def apply_change_script(
        self,
        script: VersionedScript | RepeatableScript | AlwaysScript,
        script_content: str,
        dry_run: bool,
        logger: structlog.BoundLogger,
    ) -> None:
        if dry_run:
            logger.debug("Running in dry-run mode. Skipping execution")
            return
        logger.info("Applying change script")
        # Define a few other change related variables
        # noinspection PyTypeChecker
        checksum = hashlib.sha224(script_content.encode("utf-8")).hexdigest()
        execution_time = 0
        status = "Success"

        # Execute the contents of the script
        if len(script_content) > 0:
            start = time.time()
            self.reset_session(logger=logger)
            self.reset_query_tag(extra_tag=script.name, logger=logger)
            try:
                self.execute_snowflake_query(query=script_content, logger=logger)
            except Exception as e:
                raise Exception(f"Failed to execute {script.name}") from e
            self.reset_query_tag(logger=logger)
            self.reset_session(logger=logger)
            end = time.time()
            execution_time = round(end - start)

        # Compose and execute the insert statement to the log file
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
                '{getattr(script, "version", "")}',
                '{script.description}',
                '{script.name}',
                '{script.type}',
                '{checksum}',
                {execution_time},
                '{status}',
                '{self.user}',
                CURRENT_TIMESTAMP
            );
        """
        self.execute_snowflake_query(dedent(query), logger=logger)
