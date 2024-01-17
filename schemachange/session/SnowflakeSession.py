import hashlib
import time

import snowflake.connector
from pandas import DataFrame

from schemachange.Config import DeployConfig
from schemachange.SecretManager import SecretManager
from schemachange.session.Credential import SomeCredential


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

    # region Query Templates
    _q_ch_metadata = (
        "SELECT CREATED, LAST_ALTERED FROM {database_name}.INFORMATION_SCHEMA.TABLES"
        + " WHERE TABLE_SCHEMA = REPLACE('{schema_name}','\"','') AND TABLE_NAME = REPLACE('{table_name}','\"','')"
    )
    _q_ch_schema_present = (
        "SELECT COUNT(1) FROM {database_name}.INFORMATION_SCHEMA.SCHEMATA"
        + " WHERE SCHEMA_NAME = REPLACE('{schema_name}','\"','')"
    )
    _q_ch_ddl_schema = "CREATE SCHEMA {schema_name}"
    _q_ch_ddl_table = (
        "CREATE TABLE IF NOT EXISTS {database_name}.{schema_name}.{table_name} (VERSION VARCHAR, "
        + "DESCRIPTION VARCHAR, SCRIPT VARCHAR, SCRIPT_TYPE VARCHAR, CHECKSUM VARCHAR,"
        + " EXECUTION_TIME NUMBER, STATUS VARCHAR, INSTALLED_BY VARCHAR, INSTALLED_ON TIMESTAMP_LTZ)"
    )
    _q_ch_r_checksum = (
        "SELECT DISTINCT SCRIPT, FIRST_VALUE(CHECKSUM) OVER (PARTITION BY SCRIPT "
        + "ORDER BY INSTALLED_ON DESC) FROM {database_name}.{schema_name}.{table_name} WHERE SCRIPT_TYPE = 'R' AND "
        + "STATUS = 'Success'"
    )
    _q_ch_fetch = (
        "SELECT VERSION FROM {database_name}.{schema_name}.{table_name} WHERE SCRIPT_TYPE = 'V' ORDER"
        + " BY INSTALLED_ON DESC LIMIT 1"
    )
    _q_sess_tag = "ALTER SESSION SET QUERY_TAG = '{query_tag}'"
    _q_ch_log = (
        "INSERT INTO {database_name}.{schema_name}.{table_name} (VERSION, DESCRIPTION, SCRIPT, SCRIPT_TYPE, "
        + "CHECKSUM, EXECUTION_TIME, STATUS, INSTALLED_BY, INSTALLED_ON) VALUES ('{script_version}',"
        + "'{script_description}','{script_name}','{script_type}','{checksum}',{execution_time},"
        + "'{status}','{user}',CURRENT_TIMESTAMP);"
    )
    _q_set_sess_role = "USE ROLE {role};"
    _q_set_sess_database = "USE DATABASE {database};"
    _q_set_sess_schema = "USE SCHEMA {schema};"
    _q_set_sess_warehouse = "USE WAREHOUSE {warehouse};"

    # endregion Query Templates

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

    def execute_snowflake_query(self, query):
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

    def fetch_change_history_metadata(self, change_history_table):
        # This should only ever return 0 or 1 rows
        query = self._q_ch_metadata.format(**change_history_table)
        results = self.execute_snowflake_query(query)

        # Collect all the results into a list
        change_history_metadata = dict()
        for cursor in results:
            for row in cursor:
                change_history_metadata["created"] = row[0]
                change_history_metadata["last_altered"] = row[1]

        return change_history_metadata

    def create_change_history_table_if_missing(self, change_history_table):
        # Check if schema exists
        query = self._q_ch_schema_present.format(**change_history_table)
        results = self.execute_snowflake_query(query)
        schema_exists = False
        for cursor in results:
            for row in cursor:
                schema_exists = row[0] > 0

        # Create the schema if it doesn't exist
        if not schema_exists:
            query = self._q_ch_ddl_schema.format(**change_history_table)
            self.execute_snowflake_query(query)

        # Finally, create the change history table if it doesn't exist
        query = self._q_ch_ddl_table.format(**change_history_table)
        self.execute_snowflake_query(query)

    def fetch_r_scripts_checksum(self, change_history_table):
        query = self._q_ch_r_checksum.format(**change_history_table)
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

    def fetch_change_history(self, change_history_table):
        query = self._q_ch_fetch.format(**change_history_table)
        results = self.execute_snowflake_query(query)

        # Collect all the results into a list
        change_history = list()
        for cursor in results:
            for row in cursor:
                change_history.append(row[0])

        return change_history

    def reset_session(self):
        # These items are optional, so we can only reset the ones with values
        reset_query = ""
        if self.conArgs["role"]:
            reset_query += self._q_set_sess_role.format(**self.conArgs) + " "
        if self.conArgs["warehouse"]:
            reset_query += self._q_set_sess_warehouse.format(**self.conArgs) + " "
        if self.conArgs["database"]:
            reset_query += self._q_set_sess_database.format(**self.conArgs) + " "
        if self.conArgs["schema"]:
            reset_query += self._q_set_sess_schema.format(**self.conArgs) + " "

        self.execute_snowflake_query(reset_query)

    def reset_query_tag(self, extra_tag=None):
        query_tag = self.conArgs["session_parameters"]["QUERY_TAG"]
        if extra_tag:
            query_tag += f";{extra_tag}"

        self.execute_snowflake_query(self._q_sess_tag.format(query_tag=query_tag))

    def apply_change_script(self, script, script_content, change_history_table):
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
        frmt_args["checksum"] = checksum
        frmt_args["execution_time"] = execution_time
        frmt_args["status"] = status
        frmt_args["user"] = self.conArgs["user"]
        # Compose and execute the insert statement to the log file
        query = self._q_ch_log.format(**frmt_args)
        self.execute_snowflake_query(query)
