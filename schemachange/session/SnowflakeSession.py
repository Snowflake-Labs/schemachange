import hashlib
import time
from textwrap import dedent

import snowflake.connector
from pandas import DataFrame

from schemachange.Config import DeployConfig, Table, RenderConfig
from schemachange.SecretManager import SecretManager
from schemachange.session.Credential import SomeCredential, credential_factory


class SnowflakeSession:
    user: str
    account: str
    role: str | None
    warehouse: str | None
    database: str | None
    schema: str | None
    application: str
    session_parameters: dict
    oauth_config: dict | None
    autocommit: bool
    verbose: bool
    credential: SomeCredential

    """
    Manages Snowflake Interactions and authentication
    """

    def __init__(
        self,
        config: DeployConfig,
        snowflake_user: str,
        snowflake_account: str,
        snowflake_role: str,
        schemachange_version: str,
        snowflake_application_name: str,
        credential: SomeCredential,
        snowflake_warehouse: str | None = None,
        snowflake_database: str | None = None,
        snowflake_schema: str | None = None,
        query_tag: str | None = None,
    ):
        session_parameters = {"QUERY_TAG": f"schemachange {schemachange_version}"}
        if query_tag:
            session_parameters["QUERY_TAG"] += f";{config.query_tag}"

        # Retrieve Connection info from config dictionary
        self.user = snowflake_user
        self.account = snowflake_account
        self.role = snowflake_role
        self.warehouse = snowflake_warehouse
        self.database = snowflake_database
        self.schema = snowflake_schema
        self.application = snowflake_application_name
        self.session_parameters = session_parameters
        self.oauth_config = config.oauth_config
        self.autocommit = config.autocommit
        self.verbose = config.verbose
        self.con = snowflake.connector.connect(
            user=self.user,
            account=self.account,
            role=self.role,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema,
            application=self.application,
            session_parameters=self.session_parameters,
            **credential.model_dump(),
        )
        if not self.autocommit:
            self.con.autocommit(False)
        # TODO: Where does this go?
        # else:
        #     print(
        #         "Missing environment variable(s). \n"
        #         "SNOWFLAKE_PASSWORD must be defined for password authentication. \n"
        #         "SNOWFLAKE_PRIVATE_KEY_PATH and (optional) SNOWFLAKE_PRIVATE_KEY_PASSPHRASE "
        #         "must be defined for private key authentication.\n"
        #         "SNOWFLAKE_AUTHENTICATOR must be defined is using Oauth, OKTA or external Browser Authentication."
        #     )

    def __del__(self):
        if hasattr(self, "con"):
            self.con.close()

    def execute_snowflake_query(self, query: str):
        query = dedent(query)
        if self.verbose:
            print(SecretManager.global_redact(f"SQL query: {query}"))
        try:
            res = self.con.execute_string(query)
            if not self.autocommit:
                self.con.commit()
            return res
        except Exception as e:
            if not self.autocommit:
                self.con.rollback()
            raise e

    def fetch_change_history_metadata(self, change_history_table: Table) -> dict:
        # This should only ever return 0 or 1 rows
        query = f"""
            SELECT
                CREATED,
                LAST_ALTERED
            FROM {change_history_table.database_name}.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = REPLACE('{change_history_table.schema_name}','\"','')
                AND TABLE_NAME = REPLACE('{change_history_table.table_name}','\"','')
        """
        results = self.execute_snowflake_query(query)

        # Collect all the results into a list
        change_history_metadata = dict()
        for cursor in results:
            for row in cursor:
                change_history_metadata["created"] = row[0]
                change_history_metadata["last_altered"] = row[1]

        return change_history_metadata

    def create_change_history_table_if_missing(
        self, change_history_table: Table
    ) -> None:
        # Check if schema exists
        query = f"""
            SELECT
                COUNT(1)
            FROM {change_history_table.database_name}.INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME = REPLACE('{change_history_table.schema_name}','\"','')
        """
        results = self.execute_snowflake_query(query)
        schema_exists = False
        for cursor in results:
            for row in cursor:
                schema_exists = row[0] > 0

        # Create the schema if it doesn't exist
        if not schema_exists:
            query = f"CREATE SCHEMA {change_history_table.schema_name}"
            self.execute_snowflake_query(query)

        # Finally, create the change history table if it doesn't exist
        query = f"""
            CREATE TABLE IF NOT EXISTS {change_history_table.fully_qualified} (
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
        self.execute_snowflake_query(query)

    def fetch_r_scripts_checksum(self, change_history_table: Table) -> DataFrame:
        query = f"""
        SELECT DISTINCT
            SCRIPT,
            FIRST_VALUE(CHECKSUM) OVER (
                PARTITION BY SCRIPT
                ORDER BY INSTALLED_ON DESC
            )
        FROM {change_history_table.fully_qualified}
        WHERE SCRIPT_TYPE = 'R'
            AND STATUS = 'Success'
        """
        results = self.execute_snowflake_query(query)

        # Collect all the results into a dict
        d_script_checksum = DataFrame(columns=["script_name", "checksum"])
        script_names = []
        checksums = []
        for cursor in results:
            for row in cursor:
                script_names.append(row[0])
                checksums.append(row[1])

        d_script_checksum["script_name"] = script_names
        d_script_checksum["checksum"] = checksums
        return d_script_checksum

    def fetch_change_history(self, change_history_table: Table) -> list[object]:
        query = f"""
        SELECT
            VERSION
        FROM {change_history_table.fully_qualified}
        WHERE SCRIPT_TYPE = 'V'
        ORDER BY INSTALLED_ON DESC
        LIMIT 1
        """
        results = self.execute_snowflake_query(query)

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

    def apply_change_script(self, script, script_content, change_history_table: Table):
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
        frmt_args.update(change_history_table)
        # Compose and execute the insert statement to the log file
        query = f"""
            INSERT INTO {change_history_table.fully_qualified} (
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
        self.execute_snowflake_query(query)


def get_session(
    config: DeployConfig | RenderConfig,
    schemachange_version: str,
    snowflake_application_name: str,
) -> SnowflakeSession:
    config.check_for_deploy_args()
    credential = credential_factory(
        oauth_config=config.oauth_config, verbose=config.verbose
    )
    return SnowflakeSession(
        config=config,
        snowflake_user=config.snowflake_user,
        snowflake_account=config.snowflake_account,
        snowflake_role=config.snowflake_role,
        schemachange_version=schemachange_version,
        snowflake_application_name=snowflake_application_name,
        credential=credential,
        snowflake_warehouse=config.snowflake_warehouse,
        snowflake_database=config.snowflake_database,
        snowflake_schema=config.snowflake_schema,
        query_tag=config.query_tag,
    )
