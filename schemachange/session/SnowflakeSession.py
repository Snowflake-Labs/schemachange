from __future__ import annotations

import hashlib
from textwrap import indent

import snowflake.connector
import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import get_snowflake_identifier_string
from schemachange.session.Script import VersionedScript, RepeatableScript, AlwaysScript


class SnowflakeSession:
    account: str
    user: str | None  # TODO: user: str when connections.toml is enforced
    role: str | None  # TODO: role: str when connections.toml is enforced
    warehouse: str | None  # TODO: warehouse: str when connections.toml is enforced
    database: str | None  # TODO: database: str when connections.toml is enforced
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
        connection_name: str | None = None,
        connections_file_path: str | None = None,
        account: str | None = None,  # TODO: Remove when connections.toml is enforced
        user: str | None = None,  # TODO: Remove when connections.toml is enforced
        role: str | None = None,  # TODO: Remove when connections.toml is enforced
        warehouse: str | None = None,  # TODO: Remove when connections.toml is enforced
        database: str | None = None,  # TODO: Remove when connections.toml is enforced
        schema: str | None = None,  # TODO: Remove when connections.toml is enforced
        query_tag: str | None = None,
        autocommit: bool = False,
        **kwargs,  # TODO: Remove when connections.toml is enforced
    ):
        self.change_history_table = change_history_table
        self.autocommit = autocommit
        self.logger = logger

        self.session_parameters = {"QUERY_TAG": f"schemachange {schemachange_version}"}
        if query_tag:
            self.session_parameters["QUERY_TAG"] += f";{query_tag}"

        connect_kwargs = {
            "account": account,  # TODO: Remove when connections.toml is enforced
            "user": user,  # TODO: Remove when connections.toml is enforced
            "database": database,  # TODO: Remove when connections.toml is enforced
            "schema": schema,  # TODO: Remove when connections.toml is enforced
            "role": role,  # TODO: Remove when connections.toml is enforced
            "warehouse": warehouse,  # TODO: Remove when connections.toml is enforced
            "private_key_file": kwargs.get(
                "private_key_path"
            ),  # TODO: Remove when connections.toml is enforced
            "token": kwargs.get(
                "oauth_token"
            ),  # TODO: Remove when connections.toml is enforced
            "password": kwargs.get(
                "password"
            ),  # TODO: Remove when connections.toml is enforced
            "authenticator": kwargs.get(
                "authenticator"
            ),  # TODO: Remove when connections.toml is enforced
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

        # Store connection parameters for lazy HistorySession creation
        self._history_session_params = {
            "schemachange_version": schemachange_version,
            "application": application,
            "change_history_table": change_history_table,
            "logger": logger,
            "connection_name": connection_name,
            "connections_file_path": connections_file_path,
            "account": account,
            "user": user,
            "role": role,
            "warehouse": warehouse,
            "database": database,
            "schema": schema,
            "query_tag": query_tag,
            "autocommit": autocommit,
            **kwargs,
        }
        self._history_session = None

    @property
    def history_session(self):
        """Lazily create HistorySession when first accessed."""
        if self._history_session is None:
            from schemachange.session.HistorySession import HistorySession

            self._history_session = HistorySession(**self._history_session_params)
        return self._history_session

    def __del__(self):
        if hasattr(self, "con"):
            self.con.close()

    def execute_snowflake_query(
        self, query: str, logger: structlog.BoundLogger, auto_commit: bool = True
    ):
        """Execute a single SQL query using the simplest Snowflake connector method."""
        logger.debug(
            "Executing query",
            query=indent(query, prefix="\t"),
        )
        try:
            # Use the simplest method: cursor().execute() for single queries
            cursor = self.con.cursor()
            cursor.execute(query)

            # Only commit if explicitly requested and not in autocommit mode
            if auto_commit and not self.autocommit:
                self.con.commit()
            return cursor
        except Exception as e:
            if not self.autocommit:
                self.con.rollback()
            raise e
    def get_script_metadata(
        self, create_change_history_table: bool, dry_run: bool
    ) -> tuple[
        dict[str, dict[str, str | int]] | None,
        dict[str, list[str]] | None,
        str | int | None,
    ]:
        change_history_table_exists = self.history_session.change_history_table_exists(
            create_change_history_table=create_change_history_table,
            dry_run=dry_run,
        )
        if not change_history_table_exists:
            return None, None, None

        change_history, max_published_version = (
            self.history_session.fetch_versioned_scripts()
        )
        r_scripts_checksum = self.history_session.fetch_repeatable_scripts()

        self.logger.info(
            "Max applied change script version %(max_published_version)s"
            % {"max_published_version": max_published_version}
        )
        return change_history, r_scripts_checksum, max_published_version

    def reset_session(self, logger: structlog.BoundLogger):
        """Reset session context with state checking to avoid unnecessary queries."""
        # Check current state first
        current_state = self._get_current_session_state(logger)

        reset_queries = []
        # Define the session parameters to check
        session_params = ["role", "warehouse", "database", "schema"]
        reset_queries = [
            f"USE {param.upper()} IDENTIFIER('{getattr(self, param)}');"
            for param in session_params
            if getattr(self, param) and current_state.get(param) != getattr(self, param)
        ]

        if reset_queries:
            # Execute all reset queries in a single anonymous block for efficiency
            reset_block = "BEGIN\n" + "\n".join(reset_queries) + "\nEND;"
            self.execute_snowflake_query(reset_block, logger=logger)
            logger.debug("Session context reset", queries=reset_queries)
        else:
            logger.debug("Session context already correct, no reset needed")

    def _get_current_session_state(self, logger: structlog.BoundLogger) -> dict:
        """Get current session state using simple execution."""
        try:
            # Use simple execution for state checking
            cursor = self.con.cursor()
            cursor.execute(
                "SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()"
            )

            results = cursor.fetchone()
            if results:
                return {
                    "role": results[0],
                    "warehouse": results[1],
                    "database": results[2],
                    "schema": results[3],
                }

            logger.warning("Could not get current session state, assuming reset needed")
            return {}

        except Exception as e:
            logger.warning(f"Error getting session state: {e}, assuming reset needed")
            return {}

    def reset_query_tag(self, logger: structlog.BoundLogger, extra_tag=None):
        """Reset query tag with state checking to avoid unnecessary queries."""
        desired_query_tag = self.session_parameters["QUERY_TAG"]
        if extra_tag:
            desired_query_tag += f";{extra_tag}"

        # Check current query tag
        current_query_tag = self._get_current_query_tag(logger)

        if current_query_tag != desired_query_tag:
            self.execute_snowflake_query(
                f"ALTER SESSION SET QUERY_TAG = '{desired_query_tag}'", logger=logger
            )
            logger.debug(
                "Query tag reset", from_tag=current_query_tag, to_tag=desired_query_tag
            )
        else:
            logger.debug("Query tag already correct, no reset needed")

    def _get_current_query_tag(self, logger: structlog.BoundLogger) -> str:
        """Get current query tag using simple execution."""
        try:
            cursor = self.con.cursor()
            cursor.execute("SHOW PARAMETERS LIKE 'QUERY_TAG'")

            results = cursor.fetchall()
            for row in results:
                if row[0] == "QUERY_TAG":
                    return row[1] or ""

            logger.warning("Could not get current query tag, assuming reset needed")
            return ""

        except Exception as e:
            logger.warning(f"Error getting query tag: {e}, assuming reset needed")
            return ""

    def apply_change_script(
        self,
        script: VersionedScript | RepeatableScript | AlwaysScript,
        script_content: str,
        dry_run: bool,
        logger: structlog.BoundLogger,
    ) -> None:
        if dry_run:
            logger.info("Running in dry-run mode. Skipping execution")
            return

        logger.info("Applying change script")

        # Calculate checksum
        checksum = hashlib.sha224(script_content.encode("utf-8")).hexdigest()
        execution_time = 0
        status = "Success"

        # Execute the contents of the script using the new Script-based architecture
        if len(script_content) > 0:
            self.reset_session(logger=logger)
            self.reset_query_tag(extra_tag=script.name, logger=logger)

            try:
                # Use the new Script architecture for execution
                if len(script_content.strip()) > 0:
                    execution_report = script.execute(self, script_content, logger)
                    execution_time = execution_report.total_execution_time

                    # Check if any statements failed
                    if execution_report.failure_count > 0:
                        status = "Failed"
                        failed_statements = execution_report.get_failed_statements()
                        error_messages = [
                            f"Statement {stmt.statement_index}: {result.error_message}"
                            for stmt, result in failed_statements
                        ]
                        raise Exception(
                            f"Script {script.name} failed: {'; '.join(error_messages)}"
                        )
                    else:
                        logger.info(f"Successfully applied {script.name}")
                else:
                    logger.info(f"Script {script.name} is empty, skipping execution")
                    status = "Success"

            except Exception as e:
                status = "Failed"
                raise Exception(f"Failed to execute {script.name}: {e}") from e
            finally:
                self.reset_query_tag(logger=logger)
                self.reset_session(logger=logger)

        # Use history session to insert the record
        self.history_session.insert_change_record(
            version=getattr(script, "version", ""),
            description=script.description,
            script_name=script.name,
            script_type=script.type,
            checksum=checksum,
            execution_time=execution_time,
            status=status,
            installed_by=self.user,
            logger=logger,
        )

    def fetch_change_history_metadata(self) -> dict:
        """Fetch metadata about the change history table."""
        return self.history_session.fetch_change_history_metadata()
