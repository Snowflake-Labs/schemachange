import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
import textwrap
import time
import warnings
from typing import Dict, Any, Optional, Set
import jinja2
import jinja2.ext
import requests
import snowflake.connector
import yaml
import logging
import logging.config
import rich
from sqlglot import parse, parse_one, exp
from sqlglot.optimizer.scope import build_scope
from rich_argparse import RawTextRichHelpFormatter
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from jinja2.loaders import BaseLoader

log = logging.getLogger(__name__)


# region Global Variables
# metadata
_schemachange_version = "3.7.0"
_config_file_name = "schemachange-config.yml"
_metadata_database_name = "METADATA"
_metadata_schema_name = "SCHEMACHANGE"
_metadata_table_name = "CHANGE_HISTORY"
_snowflake_application_name = "schemachange"

# messages
_err_jinja_env_var = (
    "Could not find environmental variable %s and no default" + " value was provided"
)
_err_oauth_tk_nm = "Response Json contains keys: {keys} \n but not {key}"
_err_oauth_tk_err = "\n error description: {desc}"
_err_no_auth_mthd = (
    "Unable to find connection credentials for Okta, private key,  "
    + "password, Oauth or Browser authentication"
)
_err_unsupported_auth_mthd = (
    "'{unsupported_authenticator}' is not supported authenticator option. "
    + "Choose from externalbrowser, oauth, https://<subdomain>.okta.com. Using default value = 'snowflake'"
)
_warn_password = (
    "The SNOWSQL_PWD environment variable is deprecated and will"
    + " be removed in a later version of schemachange. Please use SNOWFLAKE_PASSWORD instead."
)
_warn_password_dup = (
    "Environment variables SNOWFLAKE_PASSWORD and SNOWSQL_PWD are "
    + " both present, using SNOWFLAKE_PASSWORD"
)
_err_args_missing = (
    "Missing config values. The following config values are required: %s "
)
_err_env_missing = (
    "Missing environment variable(s). \nSNOWFLAKE_PASSWORD must be defined for "
    + "password authentication. \nSNOWFLAKE_PRIVATE_KEY_PATH and (optional) "
    + "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE must be defined for private key authentication. "
    + "\nSNOWFLAKE_AUTHENTICATOR must be defined is using Oauth, OKTA or external Browser Authentication."
)
_log_config_details = (
    "Using Snowflake account {snowflake_account}\nUsing default role "
    + "{snowflake_role}\nUsing default warehouse {snowflake_warehouse}\nUsing default "
    + "database {snowflake_database}\n"
    + "schema {snowflake_schema}"
)
_log_ch_use = (
    "Using change history table {database_name}.{schema_name}.{table_name} "
    + "(last altered {last_altered})"
)
_log_ch_create = (
    "Created change history table {database_name}.{schema_name}.{table_name}"
)
_err_ch_missing = (
    "Unable to find change history table {database_name}.{schema_name}.{table_name}"
)
_log_ch_max_version = (
    "Max applied change script version: {max_published_version_display}"
)
_log_skip_v = (
    "Skipping change script {script_name} because it's older than the most recently "
    + "applied change ({max_published_version})"
)
_log_skip_r = (
    "Skipping change script {script_name} because there is no change since the last "
    + "execution"
)
_log_apply = "Applying change script {script_name}"
_log_apply_set_complete = (
    "Successfully applied {scripts_applied} change scripts (skipping "
    + "{scripts_skipped}) \nCompleted successfully"
)
_err_vars_config = "vars did not parse correctly, please check its configuration"
_err_vars_reserved = (
    "The variable schemachange has been reserved for use by schemachange, "
    + "please use a different name"
)
_err_invalid_folder = "Invalid {folder_type} folder: {path}"
_err_dup_scripts = (
    "The script name {script_name} exists more than once (first_instance "
    + "{first_path}, second instance {script_full_path})"
)
_err_dup_scripts_version = (
    "The script version {script_version} exists more than once "
    + "(second instance {script_full_path})"
)
_err_invalid_cht = "Invalid change history table name: %s"
_log_auth_type = "Proceeding with %s authentication"
_log_pk_enc = "No private key passphrase provided. Assuming the key is not encrypted."
_log_okta_ep = "Okta Endpoint: %s"
_log_current_session_id = "Current session ID: {current_session_id}"

# endregion Global Variables


class JinjaEnvVar(jinja2.ext.Extension):
    """
    Extends Jinja Templates with access to environmental variables
    """

    def __init__(self, environment: jinja2.Environment):
        super().__init__(environment)

        # add globals
        environment.globals["env_var"] = JinjaEnvVar.env_var

    @staticmethod
    def env_var(env_var: str, default: Optional[str] = None) -> str:
        """
        Returns the value of the environmental variable or the default.
        """
        result = default
        if env_var in os.environ:
            result = os.environ[env_var]

        if result is None:
            raise ValueError(_err_jinja_env_var % env_var)

        return result


class JinjaTemplateProcessor:
    _env_args = {
        "undefined": jinja2.StrictUndefined,
        "autoescape": False,
        "extensions": [JinjaEnvVar],
    }

    def __init__(self, project_root: str, modules_folder: str = None):
        loader: BaseLoader
        if modules_folder:
            loader = jinja2.ChoiceLoader(
                [
                    jinja2.FileSystemLoader(project_root),
                    jinja2.PrefixLoader(
                        {"modules": jinja2.FileSystemLoader(modules_folder)}
                    ),
                ]
            )
        else:
            loader = jinja2.FileSystemLoader(project_root)
        self.__environment = jinja2.Environment(loader=loader, **self._env_args)
        self.__project_root = project_root

    def list(self):
        return self.__environment.list_templates()

    def override_loader(self, loader: jinja2.BaseLoader):
        # to make unit testing easier
        self.__environment = jinja2.Environment(loader=loader, **self._env_args)

    def render(self, script: str, vars: Dict[str, Any], verbose: bool) -> str:
        if not vars:
            vars = {}
        # jinja needs posix path
        posix_path = pathlib.Path(script).as_posix()
        template = self.__environment.get_template(posix_path)
        content = template.render(**vars).strip()
        content = content[:-1] if content.endswith(";") else content
        return content

    def relpath(self, file_path: str):
        return os.path.relpath(file_path, self.__project_root)


class SecretManager:
    """
    Provides the ability to redact secrets
    """

    __singleton: "SecretManager"

    @staticmethod
    def get_global_manager() -> "SecretManager":
        return SecretManager.__singleton

    @staticmethod
    def set_global_manager(global_manager: "SecretManager"):
        SecretManager.__singleton = global_manager

    @staticmethod
    def global_redact(context: str) -> str:
        """
        redacts any text that has been classified a secret
        using the global SecretManager instance.
        """
        return SecretManager.__singleton.redact(context)

    def __init__(self):
        self.__secrets = set()

    def clear(self):
        self.__secrets = set()

    def add(self, secret: str):
        if secret:
            self.__secrets.add(secret)

    def add_range(self, secrets: Set[str]):
        if secrets:
            self.__secrets = self.__secrets | secrets

    def redact(self, context: str) -> str:
        """
        redacts any text that has been classified a secret
        """
        redacted = context
        if redacted:
            for secret in self.__secrets:
                redacted = redacted.replace(secret, "*" * len(secret))
        return redacted


class SnowflakeSchemachangeSession:
    """
    Manages Snowflake Interactions and authentication
    """

    # region Query Templates
    _q_ch_metadata = (
        "SELECT CREATED, LAST_ALTERED FROM {database_name}.INFORMATION_SCHEMA.TABLES"
        + " WHERE TABLE_SCHEMA = REPLACE('{schema_name}','\"','') AND TABLE_NAME = replace('{table_name}','\"','')"
    )
    _q_ch_schema_present = (
        "SELECT COUNT(1) FROM {database_name}.INFORMATION_SCHEMA.SCHEMATA"
        + " WHERE SCHEMA_NAME = REPLACE('{schema_name}','\"','')"
    )
    _q_ch_ddl_schema = "CREATE SCHEMA IF NOT EXISTS {schema_name}"
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
        + "CHECKSUM, EXECUTION_TIME, STATUS, INSTALLED_BY, INSTALLED_ON) values ('{script_version}',"
        + "'{script_description}','{script_name}','{script_type}','{checksum}',{execution_time},"
        + "'{status}','{user}',CURRENT_TIMESTAMP);"
    )
    _q_set_sess_role = "USE ROLE IDENTIFIER('{role}');"
    _q_set_sess_database = "USE DATABASE IDENTIFIER('{database}');"
    _q_set_sess_schema = "USE SCHEMA IDENTIFIER('{schema}');"
    _q_set_sess_warehouse = "USE WAREHOUSE IDENTIFIER('{warehouse}');"
    # endregion Query Templates

    def __init__(self, config):
        # Retreive Connection info from config dictionary
        self.conArgs = self.get_snowflake_params(config)

        self.oauth_config = config["oauth_config"]
        self.autocommit = config["autocommit"]
        self.verbose = config["verbose"]
        if self.set_connection_args():
            log.info(self._q_set_sess_role.format(**self.conArgs))
            log.info(self._q_set_sess_warehouse.format(**self.conArgs))
            log.info(self._q_set_sess_database.format(**self.conArgs))
            log.info(self._q_set_sess_schema.format(**self.conArgs))
            self.con = snowflake.connector.connect(**self.conArgs)
            log.info(
                _log_current_session_id.format(current_session_id=self.con.session_id)
            )
            # Setting session context

            if not self.autocommit:
                self.con.autocommit(False)
        else:
            log.error(_err_env_missing)

    def __del__(self):
        if hasattr(self, "con"):
            self.con.close()

    def get_snowflake_params(self, config):
        session_parameters = {"QUERY_TAG": "schemachange %s" % _schemachange_version}
        if config["query_tag"]:
            session_parameters["QUERY_TAG"] += ";%s" % config["query_tag"]

        return {
            "user": config["snowflake_user"],
            "account": config["snowflake_account"],
            "role": get_snowflake_identifier_string(
                config["snowflake_role"], "snowflake_role"
            ),
            "warehouse": get_snowflake_identifier_string(
                config["snowflake_warehouse"], "snowflake_warehouse"
            ),
            "database": get_snowflake_identifier_string(
                config["snowflake_database"], "snowflake_database"
            ),
            "schema": get_snowflake_identifier_string(
                config["snowflake_schema"], "snowflake_schema"
            ),
            "application": _snowflake_application_name,
            "session_parameters": session_parameters,
        }

    def get_oauth_token(self):
        req_info = {
            "url": self.oauth_config["token-provider-url"],
            "headers": self.oauth_config["token-request-headers"],
            "data": self.oauth_config["token-request-payload"],
        }
        token_name = self.oauth_config["token-response-name"]
        response = requests.post(**req_info)
        resJsonDict = json.loads(response.text)
        try:
            return resJsonDict[token_name]
        except KeyError:
            errormessage = _err_oauth_tk_nm.format(
                keys=", ".join(resJsonDict.keys()), key=token_name
            )
            # if there is an error passed with the reponse include that
            if "error_description" in resJsonDict.keys():
                errormessage += _err_oauth_tk_err.format(
                    desc=resJsonDict["error_description"]
                )
            raise KeyError(errormessage)

    def set_connection_args(self):
        # Password authentication is the default
        snowflake_password = None
        default_authenticator = "snowflake"
        if os.getenv("SNOWFLAKE_PASSWORD") is not None and os.getenv(
            "SNOWFLAKE_PASSWORD"
        ):
            snowflake_password = os.getenv("SNOWFLAKE_PASSWORD")

        # Check legacy/deprecated env variable
        if os.getenv("SNOWSQL_PWD") is not None and os.getenv("SNOWSQL_PWD"):
            if snowflake_password:
                warnings.warn(_warn_password_dup, DeprecationWarning)
            else:
                warnings.warn(_warn_password, DeprecationWarning)
                snowflake_password = os.getenv("SNOWSQL_PWD")

        snowflake_authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR")

        if snowflake_authenticator:
            # Determine the type of Authenticator
            # OAuth based authentication
            if snowflake_authenticator.lower() == "oauth":
                oauth_token = self.get_oauth_token()

                log.debug(_log_auth_type % "Oauth Access Token")

                self.conArgs["token"] = oauth_token
                self.conArgs["authenticator"] = "oauth"
            # External Browswer based SSO
            elif snowflake_authenticator.lower() == "externalbrowser":
                self.conArgs["authenticator"] = "externalbrowser"
                log.debug(_log_auth_type % "External Browser")

            # IDP based Authentication, limited to Okta
            elif snowflake_authenticator.lower()[:8] == "https://":
                log.debug(_log_auth_type % "Okta")
                log.debug(_log_okta_ep % snowflake_authenticator)

                self.conArgs["password"] = snowflake_password
                self.conArgs["authenticator"] = snowflake_authenticator.lower()

            elif snowflake_authenticator.lower() == "snowflake":
                self.conArgs["authenticator"] = default_authenticator
            # if authenticator is not a supported method or the authenticator variable is defined but not specified
            else:
                # defaulting to snowflake as authenticator
                log.debug(
                    _err_unsupported_auth_mthd.format(
                        unsupported_authenticator=snowflake_authenticator
                    )
                )
                self.conArgs["authenticator"] = default_authenticator
        else:
            # default authenticator to snowflake
            self.conArgs["authenticator"] = default_authenticator

        if self.conArgs["authenticator"].lower() == default_authenticator:
            # Giving preference to password based authentication when both private key and password are specified.
            if snowflake_password:
                log.debug(_log_auth_type % "password")
                self.conArgs["password"] = snowflake_password

            elif os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", ""):
                log.debug(_log_auth_type % "private key")

                private_key_password = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "")
                if private_key_password:
                    private_key_password = private_key_password.encode()
                else:
                    private_key_password = None
                    log.debug(_log_pk_enc)
                with open(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"], "rb") as key:
                    p_key = serialization.load_pem_private_key(
                        key.read(),
                        password=private_key_password,
                        backend=default_backend(),
                    )

                pkb = p_key.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )

                self.conArgs["private_key"] = pkb
            else:
                raise NameError(_err_no_auth_mthd)

        return True

    def execute_snowflake_query(self, query):
        log.debug(SecretManager.global_redact("SQL query: %s" % query))
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

    def fetch_r_scripts_checksum(self, change_history_table) -> Dict[str, str]:
        """
        Fetches the checksum of the last executed R script from the change history table.
        return: a dictionary with the script name as key and the last successfully installed script checksum as value
        """
        # Note: Query only fetches last successfully installed checksum for R scripts
        query = self._q_ch_r_checksum.format(**change_history_table)
        results = self.execute_snowflake_query(query)

        # Collect all the results into a dict
        d_script_checksum = {}
        for cursor in results:
            for row in cursor:
                d_script_checksum[row[0]] = row[1]

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

    def baseline_change_script(self, script, checksum, change_history_table):
        """
        Baselines the change history table with the provided script and checksum
        """
        frmt_args = script.copy()
        frmt_args.update(change_history_table)
        frmt_args["checksum"] = checksum
        frmt_args["execution_time"] = 0
        frmt_args["status"] = "Baseline"
        frmt_args["user"] = self.conArgs["user"]

        # Compose and execute the insert statement to the log file
        query = self._q_ch_log.format(**frmt_args)
        self.execute_snowflake_query(query)


def common_command_init(config):
    """
    Common initialization for both the deploy and baseline commands
    """
    # Make sure we have the required connection info, all of the below needs to be present.
    req_args = {
        "snowflake_account",
        "snowflake_user",
        "snowflake_role",
        "snowflake_warehouse",
    }
    provided_args = {k: v for (k, v) in config.items() if v}
    missing_args = req_args - provided_args.keys()
    if len(missing_args) > 0:
        raise ValueError(
            _err_args_missing % ", ".join({s.replace("_", " ") for s in missing_args})
        )

    # ensure an authentication method is specified / present. one of the below needs to be present.
    req_env_var = {
        "SNOWFLAKE_PASSWORD",
        "SNOWSQL_PWD",
        "SNOWFLAKE_PRIVATE_KEY_PATH",
        "SNOWFLAKE_AUTHENTICATOR",
    }
    if len(req_env_var - dict(os.environ).keys()) == len(req_env_var):
        raise ValueError(_err_env_missing)

    # Log some additional details
    if config["dry_run"]:
        log.info("Running in dry-run mode")
    log.info(_log_config_details.format(**config))

    # connect to snowflake and maintain connection
    session = SnowflakeSchemachangeSession(config)

    # Deal with the change history table (create if specified)
    change_history_table = get_change_history_table_details(
        config["change_history_table"]
    )
    change_history_metadata = session.fetch_change_history_metadata(
        change_history_table
    )
    if change_history_metadata:
        log.info(
            _log_ch_use.format(
                last_altered=change_history_metadata["last_altered"],
                **change_history_table,
            )
        )
    elif config["create_change_history_table"]:
        # Create the change history table (and containing objects) if it don't exist.
        if not config["dry_run"]:
            session.create_change_history_table_if_missing(change_history_table)
        log.info(_log_ch_create.format(**change_history_table))
    else:
        raise ValueError(_err_ch_missing.format(**change_history_table))

    # Find the max published version
    max_published_version = ""

    change_history = None
    r_scripts_checksum = None
    if (config["dry_run"] and change_history_metadata) or not config["dry_run"]:
        change_history = session.fetch_change_history(change_history_table)
        r_scripts_checksum = session.fetch_r_scripts_checksum(change_history_table)

    if change_history:
        max_published_version = change_history[0]
    max_published_version_display = max_published_version
    if max_published_version_display == "":
        max_published_version_display = "None"
    log.info(
        _log_ch_max_version.format(
            max_published_version_display=max_published_version_display
        )
    )

    # Find all scripts in the root folder (recursively) and sort them correctly
    all_scripts = get_all_scripts_recursively(config["root_folder"], config["verbose"])
    all_script_names = list(all_scripts.keys())
    # Sort scripts such that versioned scripts get applied first and then the repeatable ones.
    all_script_names_sorted = (
        sorted_alphanumeric([script for script in all_script_names if script[0] == "V"])
        + sorted_alphanumeric(
            [script for script in all_script_names if script[0] == "R"]
        )
        + sorted_alphanumeric(
            [script for script in all_script_names if script[0] == "A"]
        )
    )

    return (
        session,
        change_history_table,
        all_scripts,
        all_script_names_sorted,
        r_scripts_checksum,
        max_published_version,
    )


def deploy_command(config):
    # Run the common command initialization
    (
        session,
        change_history_table,
        all_scripts,
        all_script_names_sorted,
        r_scripts_checksum,
        max_published_version,
    ) = common_command_init(config)

    scripts_skipped = 0
    scripts_applied = 0

    checksum_current = None
    checksum_last = None
    # Loop through each script in order and apply any required changes
    for script_name in all_script_names_sorted:
        script = all_scripts[script_name]

        # Apply a versioned-change script only if the version is newer than the most recent change in the database
        # Apply any other scripts, i.e. repeatable scripts, irrespective of the most recent change in the database
        if script_name[0] == "V" and get_alphanum_key(
            script["script_version"]
        ) <= get_alphanum_key(max_published_version):
            log.debug(
                _log_skip_v.format(
                    max_published_version=max_published_version, **script
                )
            )
            scripts_skipped += 1
            continue

        # Always process with jinja engine
        jinja_processor = JinjaTemplateProcessor(
            project_root=config["root_folder"], modules_folder=config["modules_folder"]
        )
        content = jinja_processor.render(
            jinja_processor.relpath(script["script_full_path"]),
            config["vars"],
            config["verbose"],
        )

        # Apply only R scripts where the checksum changed compared to the last execution of snowchange
        if script_name[0] == "R":
            # Compute the checksum for the script
            checksum_current = hashlib.sha224(content.encode("utf-8")).hexdigest()

        # check if R file was already executed
        if r_scripts_checksum and (script_name in r_scripts_checksum):
            checksum_last = r_scripts_checksum[script_name]
        else:
            checksum_last = ""

        # check if there is a change of the checksum in the script
        if checksum_current == checksum_last:
            log.debug(_log_skip_r.format(**script))
            log.debug("Current Checksum %s" % checksum_current)
            scripts_skipped += 1
            continue

        log.info(_log_apply.format(**script))
        if not config["dry_run"]:
            session.apply_change_script(script, content, change_history_table)

        scripts_applied += 1

    log.info(
        _log_apply_set_complete.format(
            scripts_applied=scripts_applied, scripts_skipped=scripts_skipped
        )
    )


def baseline_command(config):
    # Run the common initialization
    (
        session,
        change_history_table,
        all_scripts,
        all_script_names_sorted,
        r_scripts_checksum,
        max_published_version,
    ) = common_command_init(config)

    if max_published_version != "":
        raise ValueError(
            "Cannot baseline the change history table if records already exist"
        )

    # Remove prefix 'V' from baseline version if present
    if config["baseline_version"] and config["baseline_version"][0].upper() == "V":
        config["baseline_version"] = config["baseline_version"][1:]

    log.info(
        f"Baselining change history table at version [{config['baseline_version']}]"
    )

    scripts_baselined = 0

    for script_name in all_script_names_sorted:
        script = all_scripts[script_name]

        # Create a baseline for versioned scripts that are older than or
        # equal to the baseline version
        script_version = get_alphanum_key(script["script_version"])
        baseline_version = get_alphanum_key(config["baseline_version"])
        if script_name[0] == "V" and (script_version <= baseline_version):
            log.debug("Creating baseline for script %s" % script_name)
        elif script_name[0] == "V" and (script_version > baseline_version):
            log.debug("Skipping script newer than baseline %s" % script_name)

            # Skip to the next script
            continue

        # Always process with jinja engine
        jinja_processor = JinjaTemplateProcessor(
            project_root=config["root_folder"], modules_folder=config["modules_folder"]
        )
        content = jinja_processor.render(
            jinja_processor.relpath(script["script_full_path"]),
            config["vars"],
            config["verbose"],
        )

        if not config["dry_run"]:
            if script_name[0] == "R" and config["no_unversioned_checksum"]:
                # Do not compute the checksum for the script
                checksum = ""
            else:
                # Compute the checksum for the script
                checksum = hashlib.sha224(content.encode("utf-8")).hexdigest()

            # Write baseline history records
            session.baseline_change_script(script, checksum, change_history_table)
        else:
            log.info(
                "Dry-run, Skipping change history table update for %s " % script_name
            )
            continue

        scripts_baselined += 1

    log.info("Wrote %s baseline scripts to change history table" % scripts_baselined)


def get_dynamic_table_depends(sql: str) -> list[str]:
    """
    Get the list of tables that the provided SQL depends on.
    Typically used to determine dependencies for a dynamic table or view.
    """

    parsed_statements = parse(sql, dialect="snowflake")

    # Only process statements which create dynamic tables or views
    for statement in parsed_statements:
        # if statement.find_all(exp.Create):
        if isinstance(statement, exp.Create):
            #            formatted_sql_query = statement.sql(
            #               normalize=False, pad=4, indent=4, dialect="snowflake", pretty=True
            #           )
            #            print(formatted_sql_query)

            #            print(statement)

            # Get the table name we're creating
            #            print(repr(statement))
            print(statement.this)

            root = build_scope(statement)

            #            for scope in root.traverse():
            #                print(scope)

            # Taken from the sqlglot documentation
            tables = [
                source
                # Traverse the Scope tree, not the AST
                for scope in root.traverse()
                # `selected_sources` contains sources that have been selected in this scope, e.g. in a FROM or JOIN clause.
                # `alias` is the name of this source in this particular scope.
                # `node` is the AST node instance
                # if the selected source is a subquery (including common table expressions),
                #     then `source` will be the Scope instance for that subquery.
                # if the selected source is a table,
                #     then `source` will be a Table instance.
                for alias, (node, source) in scope.selected_sources.items()
                if isinstance(source, exp.Table)
            ]

            table_strings = []
            for table in tables:
                table_strings.append(str(table.db) + "." + str(table.this))
                # print(repr(table))

            # Now make the list of tables unique
            uniq_tables = list(set(table_strings))
            print(uniq_tables)


def format_sql(content):
    """
    Parses and formats the provided SQL content.
    """
    #    from sqlglot import parse

    parsed_statements = parse(content, dialect="snowflake")
    formatted_sql_queries = ""

    for statement in parsed_statements:
        formatted_sql_query = statement.sql(
            normalize=False, pad=4, indent=4, dialect="snowflake", pretty=True
        )

        # Add additional whitespace around multi-line queries
        if formatted_sql_query.count("\n") > 1:
            formatted_sql_queries += "\n" + formatted_sql_query + ";\n\n"
        else:
            formatted_sql_queries += formatted_sql_query + ";\n"

    return formatted_sql_queries


def render_command(config, script_path):
    """
    Renders the provided script.

    Note: does not apply secrets filtering.
    """
    # Validate the script file path
    script_path = os.path.abspath(script_path)
    if not os.path.isfile(script_path):
        raise ValueError(
            _err_invalid_folder.format(folder_type="script_path", path=script_path)
        )
    # Always process with jinja engine
    jinja_processor = JinjaTemplateProcessor(
        project_root=config["root_folder"], modules_folder=config["modules_folder"]
    )
    content = jinja_processor.render(
        jinja_processor.relpath(script_path), config["vars"], config["verbose"]
    )

    checksum = hashlib.sha224(content.encode("utf-8")).hexdigest()
    log.info("Checksum %s" % checksum)

    if config["format_sql"]:
        #        content = format_sql(content)
        get_dynamic_table_depends(content)


#    if config["pretty"]:
#        from rich.console import Console
#        from rich.syntax import Syntax
#
#        console = Console()
#        syntax = Syntax(code=content, lexer="sql")
#        console.print(syntax)
#    else:
#        print(content)


def alphanum_convert(text: str):
    result = None
    if text.isdigit():
        result = int(text)
    else:
        result = text.lower()
    return result


# This function will return a list containing the parts of the key (split by number parts)
# Each number is converted to and integer and string parts are left as strings
# This will enable correct sorting in python when the lists are compared
# e.g. get_alphanum_key('1.2.2') results in ['', 1, '.', 2, '.', 2, '']
def get_alphanum_key(key):
    alphanum_key = [alphanum_convert(c) for c in re.split("([0-9]+)", key)]
    return alphanum_key


def sorted_alphanumeric(data):
    return sorted(data, key=get_alphanum_key)


def load_schemachange_config(config_file_path: str) -> Dict[str, Any]:
    """
    Loads the schemachange config file and processes with jinja templating engine
    """
    config = dict()

    # First read in the yaml config file, if present
    if os.path.isfile(config_file_path):
        with open(config_file_path) as config_file:
            # Run the config file through the jinja engine to give access to environmental variables
            # The config file does not have the same access to the jinja functionality that a script
            # has.
            config_template = jinja2.Template(
                config_file.read(),
                undefined=jinja2.StrictUndefined,
                extensions=[JinjaEnvVar],
            )

            # The FullLoader parameter handles the conversion from YAML scalar values to Python the dictionary format
            config = yaml.load(config_template.render(), Loader=yaml.FullLoader)
        log.info("Using config file: %s" % config_file_path)
    return config


def get_schemachange_config(
    config_file_path,
    root_folder,
    modules_folder,
    snowflake_account,
    snowflake_user,
    snowflake_role,
    snowflake_warehouse,
    snowflake_database,
    snowflake_schema,
    change_history_table,
    vars,
    create_change_history_table,
    baseline_version,
    no_unversioned_checksum,
    pretty,
    format_sql,
    log_format,
    autocommit,
    verbose,
    silent,
    dry_run,
    query_tag,
    oauth_config,
    **kwargs,
):
    # create cli override dictionary
    # Could refactor to just pass Args as a dictionary?
    # **kwargs inlcuded to avoid complaints about unexpect arguments from arg parser eg:subcommand
    cli_inputs = {
        "root_folder": root_folder,
        "modules_folder": modules_folder,
        "snowflake_account": snowflake_account,
        "snowflake_user": snowflake_user,
        "snowflake_role": snowflake_role,
        "snowflake_warehouse": snowflake_warehouse,
        "snowflake_database": snowflake_database,
        "snowflake_schema": snowflake_schema,
        "change_history_table": change_history_table,
        "vars": vars,
        "create_change_history_table": create_change_history_table,
        "no_unversioned_checksum": no_unversioned_checksum,
        "baseline_version": baseline_version,
        "pretty": pretty,
        "format_sql": format_sql,
        "log_format": log_format,
        "autocommit": autocommit,
        "verbose": verbose,
        "silent": silent,
        "dry_run": dry_run,
        "query_tag": query_tag,
        "oauth_config": oauth_config,
    }
    cli_inputs = {k: v for (k, v) in cli_inputs.items() if v}

    # load YAML inputs and convert kebabs to snakes
    config = {
        k.replace("-", "_"): v
        for (k, v) in load_schemachange_config(config_file_path).items()
    }
    # set values passed into the cli Overriding values in config file
    config.update(cli_inputs)

    # create Default values dictionary
    config_defaults = {
        "root_folder": os.path.abspath("."),
        "modules_folder": None,
        "snowflake_account": None,
        "snowflake_user": None,
        "snowflake_role": None,
        "snowflake_warehouse": None,
        "snowflake_database": None,
        "snowflake_schema": None,
        "change_history_table": None,
        "vars": {},
        "create_change_history_table": False,
        "baseline_version": "",
        "pretty": False,
        "format_sql": False,
        "log_format": "basic",
        "no_unversioned_checksum": False,
        "autocommit": False,
        "verbose": False,
        "silent": False,
        "dry_run": False,
        "query_tag": None,
        "oauth_config": None,
    }
    # insert defualt values for items not populated
    config.update(
        {k: v for (k, v) in config_defaults.items() if k not in config.keys()}
    )

    # Validate folder paths
    if "root_folder" in config:
        config["root_folder"] = os.path.abspath(config["root_folder"])
    if not os.path.isdir(config["root_folder"]):
        raise ValueError(
            _err_invalid_folder.format(folder_type="root", path=config["root_folder"])
        )

    if config["modules_folder"]:
        config["modules_folder"] = os.path.abspath(config["modules_folder"])
        if not os.path.isdir(config["modules_folder"]):
            raise ValueError(
                _err_invalid_folder.format(
                    folder_type="modules", path=config["modules_folder"]
                )
            )
    if config["vars"]:
        # if vars is configured wrong in the config file it will come through as a string
        if not isinstance(config["vars"], dict):
            raise ValueError(_err_vars_config)

        # the variable schema change has been reserved
        if "schemachange" in config["vars"]:
            raise ValueError(_err_vars_reserved)

    return config


def get_snowflake_identifier_string(input_value: str, input_type: str) -> str:
    pattern = re.compile(
        r"^[\w]+$"
    )  # Words with alphanumeric characters and underscores only.
    result = ""

    if input_value is None:
        result = None
    elif pattern.match(input_value):
        result = input_value
    elif input_value.startswith('"') and input_value.endswith('"'):
        result = input_value
    elif input_value.startswith('"') and not input_value.endswith('"'):
        raise ValueError(
            f"Invalid {input_type}: {input_value}. Missing ending double quote"
        )
    elif not input_value.startswith('"') and input_value.endswith('"'):
        raise ValueError(
            f"Invalid {input_type}: {input_value}. Missing beginning double quote"
        )
    else:
        result = f'"{input_value}"'

    return result


def get_all_scripts_recursively(root_directory, verbose):
    all_files = dict()
    all_versions = list()
    # Walk the entire directory structure recursively
    for directory_path, directory_names, file_names in os.walk(root_directory):
        for file_name in file_names:
            file_full_path = os.path.join(directory_path, file_name)
            script_name_parts = re.search(
                r"^([V])(.+?)__(.+?)\.(?:sql|sql.jinja)$",
                file_name.strip(),
                re.IGNORECASE,
            )
            repeatable_script_name_parts = re.search(
                r"^([R])__(.+?)\.(?:sql|sql.jinja)$", file_name.strip(), re.IGNORECASE
            )
            always_script_name_parts = re.search(
                r"^([A])__(.+?)\.(?:sql|sql.jinja)$", file_name.strip(), re.IGNORECASE
            )

            # Set script type depending on whether it matches the versioned file naming format
            if script_name_parts is not None:
                script_type = "V"
                log.debug("Found Versioned file " + file_full_path)
            elif repeatable_script_name_parts is not None:
                script_type = "R"
                log.debug("Found Repeatable file " + file_full_path)
            elif always_script_name_parts is not None:
                script_type = "A"
                log.debug("Found Always file " + file_full_path)
            else:
                log.debug("Ignoring non-change file " + file_full_path)
                continue

            # script name is the filename without any jinja extension
            (file_part, extension_part) = os.path.splitext(file_name)
            if extension_part.upper() == ".JINJA":
                script_name = file_part
            else:
                script_name = file_name

            # Add this script to our dictionary (as nested dictionary)
            script = dict()
            script["script_name"] = script_name
            script["script_full_path"] = file_full_path
            script["script_type"] = script_type
            script["script_version"] = (
                "" if script_type in ["R", "A"] else script_name_parts.group(2)
            )
            if script_type == "R":
                script["script_description"] = (
                    repeatable_script_name_parts.group(2).replace("_", " ").capitalize()
                )
            elif script_type == "A":
                script["script_description"] = (
                    always_script_name_parts.group(2).replace("_", " ").capitalize()
                )
            else:
                script["script_description"] = (
                    script_name_parts.group(3).replace("_", " ").capitalize()
                )

            # Throw an error if the script_name already exists
            if script_name in all_files:
                raise ValueError(
                    _err_dup_scripts.format(
                        first_path=all_files[script_name]["script_full_path"], **script
                    )
                )

            all_files[script_name] = script

            # Throw an error if the same version exists more than once
            if script_type == "V":
                if script["script_version"] in all_versions:
                    raise ValueError(_err_dup_scripts_version.format(**script))
                all_versions.append(script["script_version"])

    return all_files


def get_change_history_table_details(change_history_table):
    # Start with the global defaults
    details = dict()
    details["database_name"] = _metadata_database_name
    details["schema_name"] = _metadata_schema_name
    details["table_name"] = _metadata_table_name

    # Then override the defaults if requested. The name could be in one, two or three part notation.
    if change_history_table is not None:
        table_name_parts = change_history_table.strip().split(".")
        if len(table_name_parts) == 1:
            details["table_name"] = table_name_parts[0]
        elif len(table_name_parts) == 2:
            details["table_name"] = table_name_parts[1]
            details["schema_name"] = table_name_parts[0]
        elif len(table_name_parts) == 3:
            details["table_name"] = table_name_parts[2]
            details["schema_name"] = table_name_parts[1]
            details["database_name"] = table_name_parts[0]
        else:
            raise ValueError(_err_invalid_cht % change_history_table)
    # if the object name does not include '"' raise to upper case on return
    return {k: v if '"' in v else v.upper() for (k, v) in details.items()}


def extract_config_secrets(config: Dict[str, Any]) -> Set[str]:
    """
    Extracts all secret values from the vars attributes in config
    """

    # defined as an inner/ nested function to provide encapsulation
    def inner_extract_dictionary_secrets(
        dictionary: Dict[str, Any], child_of_secrets: bool = False
    ) -> Set[str]:
        """
        Considers any key with the word secret in the name as a secret or
        all values as secrets if a child of a key named secrets.
        """
        extracted_secrets: Set[str] = set()

        if dictionary:
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    if key == "secrets":
                        extracted_secrets = (
                            extracted_secrets
                            | inner_extract_dictionary_secrets(value, True)
                        )
                    else:
                        extracted_secrets = (
                            extracted_secrets
                            | inner_extract_dictionary_secrets(value, child_of_secrets)
                        )
                elif child_of_secrets or "SECRET" in key.upper():
                    extracted_secrets.add(value.strip())
        return extracted_secrets

    extracted = set()

    if config:
        if "vars" in config:
            extracted = inner_extract_dictionary_secrets(config["vars"])
    return extracted


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        prog="schemachange",
        description="""Apply schema changes to a Snowflake account.
        Full readme at https://github.com/Snowflake-Labs/schemachange""",
        # formatter_class=argparse.RawTextHelpFormatter,
        # formatter_class=RichHelpFormatter,
        formatter_class=RawTextRichHelpFormatter,
    )
    subcommands = parser.add_subparsers(
        dest="subcommand", description="Available Schemachange operations"
    )

    parser_render = subcommands.add_parser(
        "render",
        help="Renders a script to the console",
        description="Renders a script to the console, used to check and verify jinja output from scripts.",
        formatter_class=parser.formatter_class,
    )
    parser_deploy = subcommands.add_parser(
        "deploy",
        help="Apply and log schema changes",
        description="Apply and log schema changes",
        formatter_class=parser.formatter_class,
    )
    parser_baseline = subcommands.add_parser(
        "baseline",
        help="Set baseline version and history",
        description="Set baseline version and history for existing DB to use schemachange",
        formatter_class=parser.formatter_class,
    )

    ### Render subcommand
    parser_render.add_argument("script", type=str, help="The script to render")

    ### Baseline Schema Version subcommand
    parser_baseline.add_argument(
        "--baseline-version",
        type=str,
        help="Version number for baseline",
        required=False,
    )
    parser_baseline.add_argument(
        "--no-unversioned-checksum",
        action="store_true",
        help="""Do not generate checksums for unversioned R__ scripts, causing them to be applied on subsequent run""",
        required=False,
    )

    # Initialize common subparser arguments for ALL subcommands
    for all_subparser in [parser_render, parser_deploy, parser_baseline]:
        all_subparser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Display verbose debugging details during execution (default: %(default)s)",
            required=False,
        )
        all_subparser.add_argument(
            "--silent",
            action="store_true",
            help="Silence all output except critical errors (default: %(default)s)",
            required=False,
        )
        all_subparser.add_argument(
            "--pretty",
            action="store_true",
            help="Pretty print output using Rich library (default: %(default)s)",
            required=False,
        )
        all_subparser.add_argument(
            "--format-sql",
            action="store_true",
            help="Format the SQL output using sqlparse library",
            required=False,
        )
        all_subparser.add_argument(
            "--log-format",
            type=str,
            nargs="?",
            choices=["basic", "levels", "detailed"],
            help="The format of the log output (default: %(default)s)",
            const="basic",
            default="basic",
        )
        all_subparser.add_argument(
            "--vars",
            type=json.loads,
            help="""Define values for the variables to be replaced in change scripts, given in JSON format
            (e.g. {"variable1": "value1", "variable2": "value2"})""",
            required=False,
        )
        all_subparser.add_argument(
            "-m",
            "--modules-folder",
            type=str,
            help="The modules folder for jinja macros and templates to be used across multiple scripts",
            required=False,
        )
        all_subparser.add_argument(
            "-f",
            "--root-folder",
            type=str,
            help="The root folder for the database change scripts",
            required=False,
        )
        all_subparser.add_argument(
            "--config-folder",
            type=str,
            default=".",
            help="The folder to look in for the schemachange-config.yml file (default: %(default)s)",
            required=False,
        )

    # Initialize common subparser arguments for deploy and baseline
    for common_subparser in [parser_deploy, parser_baseline]:
        common_subparser.add_argument(
            "-a",
            "--snowflake-account",
            type=str,
            help="The name of the snowflake account (e.g. xy12345.east-us-2.azure)",
            required=False,
        )
        common_subparser.add_argument(
            "-u",
            "--snowflake-user",
            type=str,
            help="The name of the snowflake user",
            required=False,
        )
        common_subparser.add_argument(
            "-r",
            "--snowflake-role",
            type=str,
            help="The name of the default role to use",
            required=False,
        )
        common_subparser.add_argument(
            "-w",
            "--snowflake-warehouse",
            type=str,
            help="The name of the default warehouse to use. Can be overridden in the change scripts.",
            required=False,
        )
        common_subparser.add_argument(
            "-d",
            "--snowflake-database",
            type=str,
            help="The name of the default database to use. Can be overridden in the change scripts.",
            required=False,
        )
        common_subparser.add_argument(
            "-s",
            "--snowflake-schema",
            type=str,
            help="The name of the default schema to use. Can be overridden in the change scripts.",
            required=False,
        )
        common_subparser.add_argument(
            "-c",
            "--change-history-table",
            type=str,
            default="METADATA.SCHEMACHANGE.CHANGE_HISTORY",
            help="""Used to override the default name of the change history table
            (default: %(default)s)""",
            required=False,
        )
        common_subparser.add_argument(
            "--create-change-history-table",
            action="store_true",
            help="Create the change history schema and table, if they do not exist (default: %(default)s)",
            required=False,
        )
        common_subparser.add_argument(
            "-ac",
            "--autocommit",
            action="store_true",
            help="Enable autocommit feature for DML commands (default: %(default)s)",
            required=False,
        )
        common_subparser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run schemachange in dry run mode (default: %(default)s)",
            required=False,
        )
        common_subparser.add_argument(
            "--query-tag",
            type=str,
            help="The string to add to the Snowflake QUERY_TAG session value for each query executed",
            required=False,
        )
        common_subparser.add_argument(
            "--oauth-config",
            type=json.loads,
            help="""Define values for the variables to Make Oauth Token requests
            (e.g. {"token-provider-url": "https//...", "token-request-payload": {"client_id": "GUID_xyz",...},... })""",
            required=False,
        )
        # TODO test CLI passing of args

    # The original parameters did not support subcommands. Check if a subcommand has been supplied
    # if not default to deploy to match original behaviour.
    args = argv[1:]
    if len(args) == 0 or (
        ("--help" not in args and "-h" not in args)
        and not any(
            subcommand in args[0].upper()
            for subcommand in ["DEPLOY", "RENDER", "BASELINE"]
        )
    ):
        args = ["deploy"] + args

    args = parser.parse_args(args)

    # Set the log format
    if args.log_format == "basic":
        format = "%(message)s"
    if args.log_format == "levels":
        format = "%(levelname)s:%(message)s"
    elif args.log_format == "detailed":
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Set the log level
    if args.verbose:
        loglevel = logging.DEBUG
    elif args.silent:
        loglevel = logging.CRITICAL
    else:
        loglevel = logging.INFO

    if args.pretty:
        from rich.logging import RichHandler

        # Install rich.traceback as the default traceback handler
        from rich.traceback import install

        # Setup logging
        logging.basicConfig(
            level=loglevel,
            format=format,
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True, markup=False)],
        )

        log = logging.getLogger("rich")

        # Enable local variable debugging in traceback
        install(show_locals=True)
    else:
        logging.basicConfig(level=loglevel, format=format, datefmt="[%X]")
        log = logging.getLogger(__name__)

    # Quiet the snowflake connector logging
    logger_blocklist = [
        "snowflake.connector",
    ]

    for module in logger_blocklist:
        logging.getLogger(module).setLevel(logging.WARNING)

    log.info("schemachange version: %s" % _schemachange_version)

    # First get the config values
    config_file_path = os.path.join(args.config_folder, _config_file_name)

    # Retreive argparser attributes as dictionary
    schemachange_args = args.__dict__
    schemachange_args["config_file_path"] = config_file_path

    # nullify expected null values for render.
    if args.subcommand == "render":
        renderoveride = {
            "snowflake_account": None,
            "snowflake_user": None,
            "snowflake_role": None,
            "snowflake_warehouse": None,
            "snowflake_database": None,
            "change_history_table": None,
            "snowflake_schema": None,
            "create_change_history_table": None,
            "no_unversioned_checksum": None,
            "baseline_version": None,
            "autocommit": None,
            "dry_run": None,
            "query_tag": None,
            "oauth_config": None,
        }
        schemachange_args.update(renderoveride)
    if args.subcommand == "deploy":
        deployoveride = {
            "no_unversioned_checksum": None,
            "baseline_version": None,
        }
        schemachange_args.update(deployoveride)
    config = get_schemachange_config(**schemachange_args)

    # setup a secret manager and assign to global scope
    sm = SecretManager()
    SecretManager.set_global_manager(sm)
    # Extract all secrets for --vars
    sm.add_range(extract_config_secrets(config))

    # Then log some details
    log.info("Using root folder %s" % config["root_folder"])
    if config["modules_folder"]:
        log.info("Using Jinja modules folder %s" % config["modules_folder"])

    # pretty print the variables in yaml style
    if config["vars"] == {}:
        log.info("Using variables: {}")
    else:
        log.info("Using variables:")
        log.info(
            textwrap.indent(
                SecretManager.global_redact(
                    yaml.dump(config["vars"], sort_keys=False, default_flow_style=False)
                ),
                prefix="  ",
            )
        )

    # Finally, execute the command
    try:
        if args.subcommand == "render":
            render_command(config, args.script)
        elif args.subcommand == "baseline":
            baseline_command(config)
        else:
            deploy_command(config)
    except Exception:
        log.error("An error occurred", exc_info=True)
        print("\n----------------------------------------\n")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
