from __future__ import annotations

import hashlib
import time
from collections import defaultdict
from textwrap import dedent, indent

import snowflake.connector
import structlog

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import get_snowflake_identifier_string
from schemachange.session.Script import AlwaysScript, RepeatableScript, VersionedScript


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
        # NOTE: connection_name and connections_file_path are no longer passed here
        # All parameters from connections.toml are merged in get_merged_config.py before creating SnowflakeSession
        account: str | None = None,  # Merged from CLI > ENV > YAML > connections.toml
        user: str | None = None,  # Merged from CLI > ENV > YAML > connections.toml
        role: str | None = None,  # Merged from CLI > ENV > YAML > connections.toml
        warehouse: str | None = None,  # Merged from CLI > ENV > YAML > connections.toml
        database: str | None = None,  # Merged from CLI > ENV > YAML > connections.toml
        schema: str | None = None,  # Merged from CLI > ENV > YAML > connections.toml
        query_tag: str | None = None,
        autocommit: bool = False,
        session_parameters: dict | None = None,  # Merged session params from CLI/ENV/YAML/connections.toml
        additional_snowflake_params: dict | None = None,
        **kwargs,  # password, authenticator, private_key_path, etc.
    ):
        self.change_history_table = change_history_table
        self.autocommit = autocommit
        self.logger = logger

        # Build schemachange's QUERY_TAG value
        # We'll apply this after connection is established to preserve any QUERY_TAG from connections.toml
        schemachange_query_tag = f"schemachange {schemachange_version}"
        if query_tag:
            schemachange_query_tag += f";{query_tag}"

        # Prepare session_parameters from CLI/ENV/YAML (already merged in get_merged_config)
        if session_parameters is None:
            session_parameters = {}

        # Start with additional_snowflake_params (lowest priority for these params)
        # These come from YAML v2 snowflake section or generic SNOWFLAKE_* env vars
        connect_kwargs = {}

        if additional_snowflake_params:
            # Convert kebab-case keys to snake_case for connector compatibility
            for key, value in additional_snowflake_params.items():
                snake_case_key = key.replace("-", "_")
                connect_kwargs[snake_case_key] = value
            self.logger.debug(
                "Using additional Snowflake parameters from YAML v2 or environment variables",
                additional_params=list(connect_kwargs.keys()),
            )

        # Explicit parameters override additional_snowflake_params
        # This ensures CLI > ENV > YAML precedence is maintained
        explicit_params = {
            "account": account,
            "user": user,
            "database": database,
            "schema": schema,
            "role": role,
            "warehouse": warehouse,
            "private_key_file": kwargs.get(
                "private_key_file"
            ),  # Already mapped from private_key_path in get_session_kwargs()
            "token": kwargs.get("token"),
            "password": kwargs.get("password"),
            "authenticator": kwargs.get("authenticator"),
            "application": application,
        }

        # Merge session_parameters (already merged from CLI/ENV/YAML/connections.toml) with schemachange's QUERY_TAG
        # session_parameters already contains merged params with precedence: CLI > ENV > YAML > connections.toml
        final_session_params = {**session_parameters}  # Start with already-merged params

        # Handle QUERY_TAG: append schemachange's tag to any existing QUERY_TAG
        # QUERY_TAG might come from connections.toml, CLI/ENV/YAML session_parameters, or query_tag argument
        if "QUERY_TAG" in final_session_params:
            final_session_params["QUERY_TAG"] += f";{schemachange_query_tag}"
        else:
            final_session_params["QUERY_TAG"] = schemachange_query_tag

        explicit_params["session_parameters"] = final_session_params

        # Merge explicit params, overriding any additional params
        connect_kwargs.update({k: v for k, v in explicit_params.items() if v is not None})

        # NOTE: We do NOT pass connection_name or connections_file_path to connect()
        # All parameters from connections.toml have already been read and merged in get_merged_config.py
        # This ensures proper precedence: CLI > ENV > YAML > connections.toml

        self.logger.debug("snowflake.connector.connect kwargs", **connect_kwargs)
        self.con = snowflake.connector.connect(**connect_kwargs)
        self.logger.info("Snowflake connection established", session_id=self.con.session_id)
        self.account = self.con.account
        self.user = get_snowflake_identifier_string(self.con.user, "user")
        self.role = get_snowflake_identifier_string(self.con.role, "role")
        self.warehouse = get_snowflake_identifier_string(self.con.warehouse, "warehouse")
        self.database = get_snowflake_identifier_string(self.con.database, "database")
        self.schema = get_snowflake_identifier_string(self.con.schema, "schema")

        if not self.autocommit:
            self.con.autocommit(False)

        # Store final merged session parameters that were passed to connect()
        # (already merged in get_merged_config with CLI > ENV > YAML > connections.toml precedence)
        self.session_parameters = explicit_params.get("session_parameters", {})

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
        change_history_metadata = {}
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
        query = f"CREATE SCHEMA IF NOT EXISTS {self.change_history_table.fully_qualified_schema_name}"
        if dry_run:
            self.logger.info(
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
            self.logger.info(
                "Running in dry-run mode. Skipping execution.",
                query=indent(dedent(query), prefix="\t"),
            )
        else:
            self.execute_snowflake_query(dedent(query), logger=self.logger)
            self.logger.info(f"Created change history table {self.change_history_table.fully_qualified}")

    def change_history_table_exists(self, create_change_history_table: bool, dry_run: bool) -> bool:
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
            raise ValueError(f"Unable to find change history table {self.change_history_table.fully_qualified}")

    def get_script_metadata(
        self, create_change_history_table: bool, initial_deployment: bool, dry_run: bool
    ) -> tuple[
        dict[str, dict[str, str | int]] | None,
        dict[str, list[str]] | None,
        str | int | None,
    ]:
        # Check if change history table exists
        change_history_metadata = self.fetch_change_history_metadata()
        table_exists = change_history_metadata is not None

        # Validate initial_deployment flag combinations
        if initial_deployment:
            if table_exists:
                raise ValueError(
                    f"--initial-deployment was specified but change history table "
                    f"{self.change_history_table.fully_qualified} already exists. "
                    f"This indicates either:\n"
                    f"  1. This is NOT an initial deployment (remove --initial-deployment)\n"
                    f"  2. The table from a previous deployment was not cleaned up"
                )
            if not create_change_history_table:
                raise ValueError("--initial-deployment requires --create-change-history-table to be true")
            # Valid initial deployment scenario
            self.logger.info(
                "Initial deployment mode: Change history table will be created " "and all scripts treated as new."
            )
            if dry_run:
                self.logger.info("Dry-run: Change history table creation and script execution will be previewed only.")
            # Proceed with table creation (the method will handle logging and creation)
            self.change_history_table_exists(
                create_change_history_table=create_change_history_table,
                dry_run=dry_run,
            )
            # Return empty metadata (all scripts are new)
            return defaultdict(dict), None, None

        # NOT initial deployment - check if table exists
        if not table_exists:
            if create_change_history_table:
                # This is the dangerous scenario - table missing but not declared as initial deployment
                error_msg = (
                    f"Change history table {self.change_history_table.fully_qualified} does not exist.\n"
                    f"If this is the initial deployment of schemachange, add --initial-deployment flag.\n"
                    f"Otherwise, this indicates a configuration error or missing infrastructure."
                )
                if dry_run:
                    self.logger.error(error_msg)
                    raise ValueError(error_msg + "\nCannot perform accurate dry-run without change history.")
                else:
                    # In non-dry-run mode, this is even more dangerous
                    self.logger.error(error_msg)
                    raise ValueError(error_msg + "\nRefusing to proceed to prevent re-applying scripts.")
            else:
                # This already errors correctly (existing behavior)
                raise ValueError(f"Unable to find change history table {self.change_history_table.fully_qualified}")

        # Table exists, log and proceed normally
        self.logger.info(
            f"Using existing change history table {self.change_history_table.fully_qualified}",
            last_altered=change_history_metadata["last_altered"],
        )

        change_history, max_published_version = self.fetch_versioned_scripts()
        r_scripts_checksum = self.fetch_repeatable_scripts()

        self.logger.info(f"Max applied change script version {max_published_version}")
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
        versions: list[str | int | None] = []
        for cursor in results:
            for version, script, checksum in cursor:
                versions.append(version if version != "" else None)
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

        self.execute_snowflake_query(f"ALTER SESSION SET QUERY_TAG = '{query_tag}'", logger=logger)

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
