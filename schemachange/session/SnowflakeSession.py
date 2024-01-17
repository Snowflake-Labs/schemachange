import hashlib
import time
from collections import defaultdict
from textwrap import dedent, indent

import snowflake.connector

from schemachange.Config import DeployConfig, Table, RenderConfig
from schemachange.SecretManager import SecretManager
from schemachange.session.Credential import SomeCredential, credential_factory


class SnowflakeSession:
    secret_manager: SecretManager
    user: str
    role: str
    warehouse: str
    database: str | None
    schema: str | None
    query_tag: str | None
    autocommit: bool
    verbose: bool
    dry_run: bool
    change_history_table: Table
    session_parameters: dict[str, str]
    conn: snowflake.connector.SnowflakeConnection

    """
    Manages Snowflake Interactions and authentication
    """

    def __init__(
        self,
        secret_manager: SecretManager,
        snowflake_user: str,
        snowflake_account: str,
        snowflake_role: str,
        snowflake_warehouse: str,
        schemachange_version: str,
        application: str,
        credential: SomeCredential,
        change_history_table: Table,
        autocommit: bool = False,
        verbose: bool = False,
        snowflake_database: str | None = None,
        snowflake_schema: str | None = None,
        query_tag: str | None = None,
        dry_run: bool = True,
    ):
        self.secret_manager = secret_manager
        self.user = snowflake_user
        self.role = snowflake_role
        self.warehouse = snowflake_warehouse
        self.database = snowflake_database
        self.schema = snowflake_schema
        self.autocommit = autocommit
        self.verbose = verbose
        self.dry_run = dry_run
        self.change_history_table = change_history_table

        self.session_parameters = {"QUERY_TAG": f"schemachange {schemachange_version}"}
        if query_tag:
            self.session_parameters["QUERY_TAG"] += f";{query_tag}"

        self.con = snowflake.connector.connect(
            user=self.user,
            account=snowflake_account,
            role=self.role,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema,
            application=application,
            session_parameters=self.session_parameters,
            **credential.model_dump(),
        )
        if not self.autocommit:
            self.con.autocommit(False)

    def __del__(self):
        if hasattr(self, "con"):
            self.con.close()

    def print_snowflake_query(self, query: str):
        if self.verbose:
            print("SQL query:")
            print(indent(self.secret_manager.redact(query), prefix="\t"))
            print()

    def execute_snowflake_query(self, query: str):
        self.print_snowflake_query(query=query)
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
        results = self.execute_snowflake_query(dedent(query))

        # Collect all the results into a list
        change_history_metadata = dict()
        for cursor in results:
            for row in cursor:
                change_history_metadata["created"] = row[0]
                change_history_metadata["last_altered"] = row[1]

        return change_history_metadata

    def create_change_history_table_if_missing(self) -> None:
        # Check if schema exists
        query = f"""\
            SELECT
                COUNT(1)
            FROM {self.change_history_table.database_name}.INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME = REPLACE('{self.change_history_table.schema_name}','\"','')
        """
        results = self.execute_snowflake_query(dedent(query))
        schema_exists = False
        for cursor in results:
            for row in cursor:
                schema_exists = row[0] > 0

        # Create the schema if it doesn't exist
        if not schema_exists:
            query = f"CREATE SCHEMA {self.change_history_table.schema_name}"
            if self.dry_run:
                print("Running in dry-run mode. Skipping execution:")
                self.print_snowflake_query(query=dedent(query))
            else:
                self.execute_snowflake_query(dedent(query))

        # Finally, create the change history table if it doesn't exist
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
        if self.dry_run:
            print("Running in dry-run mode. Skipping execution:")
            self.print_snowflake_query(query=dedent(query))
        else:
            self.execute_snowflake_query(dedent(query))

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
        results = self.execute_snowflake_query(dedent(query))

        # Collect all the results into a dict
        script_checksums: dict[str, list[str]] = defaultdict(list)
        for cursor in results:
            for script_name, checksum in cursor:
                script_checksums[script_name].append(checksum)
        return script_checksums

    def fetch_versioned_scripts(self) -> list[str | int]:
        query = f"""\
        SELECT
            VERSION
        FROM {self.change_history_table.fully_qualified}
        WHERE SCRIPT_TYPE = 'V'
        ORDER BY INSTALLED_ON DESC -- TODO: Why not order by version?
        LIMIT 1
        """
        results = self.execute_snowflake_query(dedent(query))

        # Collect all the results into a list
        change_history = list()
        for cursor in results:
            for row in cursor:
                change_history.append(row[0])

        return change_history

    def reset_session(self):
        # These items are optional, so we can only reset the ones with values
        reset_query = []
        if self.role:
            reset_query.append(f"USE ROLE {self.role};")
        if self.warehouse:
            reset_query.append(f"USE WAREHOUSE {self.warehouse};")
        if self.database:
            reset_query.append(f"USE DATABASE {self.database};")
        if self.schema:
            reset_query.append(f"USE SCHEMA {self.schema};")

        self.execute_snowflake_query("\n".join(reset_query))

    def reset_query_tag(self, extra_tag=None):
        query_tag = self.session_parameters["QUERY_TAG"]
        if extra_tag:
            query_tag += f";{extra_tag}"

        self.execute_snowflake_query(f"ALTER SESSION SET QUERY_TAG = '{query_tag}'")

    def apply_change_script(self, script, script_content) -> None:
        if self.dry_run:
            print(f"Running in dry-run mode. Skipping execution: {script.script_name}")
            return
        # Define a few other change related variables
        checksum = hashlib.sha224(script_content.encode("utf-8")).hexdigest()
        execution_time = 0
        status = "Success"

        # Execute the contents of the script
        if len(script_content) > 0:
            start = time.time()
            self.reset_session()
            self.reset_query_tag(script["script_name"])
            self.execute_snowflake_query(script_content)
            self.reset_query_tag()
            self.reset_session()
            end = time.time()
            execution_time = round(end - start)

        # Finally record this change in the change history table by gathering data
        frmt_args = script.copy()
        frmt_args.update(self.change_history_table)
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
                '{script_version}',
                '{script_description}',
                '{script_name}',
                '{script_type}',
                '{checksum}',
                {execution_time},
                '{status}',
                '{self.user}',
                CURRENT_TIMESTAMP
            );
        """
        self.execute_snowflake_query(dedent(query))


def get_session_from_config(
    config: DeployConfig | RenderConfig,
    secret_manager: SecretManager,
    schemachange_version: str,
    snowflake_application_name: str,
) -> SnowflakeSession:
    config.check_for_deploy_args()
    credential = credential_factory(
        oauth_config=config.oauth_config, verbose=config.verbose
    )
    return SnowflakeSession(
        secret_manager=secret_manager,
        snowflake_user=config.snowflake_user,
        snowflake_account=config.snowflake_account,
        snowflake_role=config.snowflake_role,
        snowflake_warehouse=config.snowflake_warehouse,
        schemachange_version=schemachange_version,
        application=snowflake_application_name,
        credential=credential,
        change_history_table=config.change_history_table,
        autocommit=config.autocommit,
        verbose=config.verbose,
        snowflake_database=config.snowflake_database,
        snowflake_schema=config.snowflake_schema,
        query_tag=config.query_tag,
        dry_run=config.dry_run,
    )
