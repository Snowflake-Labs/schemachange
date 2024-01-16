import hashlib
import json
import os
import re
import sys
import textwrap
import time
import warnings
from typing import Dict, Any, Optional, Set

import requests
import snowflake.connector
import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from pandas import DataFrame

from schemachange.Config import config_factory
from schemachange.SecretManager import SecretManager
from schemachange.JinjaTemplateProcessor import JinjaTemplateProcessor
from schemachange.get_yaml_config import get_yaml_config
from schemachange.parse_cli_args import parse_cli_args

# region Global Variables
# metadata
_schemachange_version = "3.6.1"
_metadata_database_name = "METADATA"
_metadata_schema_name = "SCHEMACHANGE"
_metadata_table_name = "CHANGE_HISTORY"
_snowflake_application_name = "schemachange"

# messages
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
    + "database {snowflake_database}"
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

# endregion Global Variables


class SnowflakeSchemachangeSession:
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

    def __init__(self, config):
        session_parameters = {"QUERY_TAG": "schemachange %s" % _schemachange_version}
        if config["query_tag"]:
            session_parameters["QUERY_TAG"] += ";%s" % config["query_tag"]

        # Retreive Connection info from config dictionary
        self.conArgs = {
            "user": config["snowflake_user"],
            "account": config["snowflake_account"],
            "role": config["snowflake_role"],
            "warehouse": config["snowflake_warehouse"],
            "database": config["snowflake_database"],
            "schema": config["snowflake_schema"],
            "application": _snowflake_application_name,
            "session_parameters": session_parameters,
        }

        self.oauth_config = config["oauth_config"]
        self.autocommit = config["autocommit"]
        self.verbose = config["verbose"]
        if self.set_connection_args():
            self.con = snowflake.connector.connect(**self.conArgs)
            if not self.autocommit:
                self.con.autocommit(False)
        else:
            print(_err_env_missing)

    def __del__(self):
        if hasattr(self, "con"):
            self.con.close()

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

                if self.verbose:
                    print(_log_auth_type % "Oauth Access Token")
                self.conArgs["token"] = oauth_token
                self.conArgs["authenticator"] = "oauth"
            # External Browswer based SSO
            elif snowflake_authenticator.lower() == "externalbrowser":
                self.conArgs["authenticator"] = "externalbrowser"
                if self.verbose:
                    print(_log_auth_type % "External Browser")
            # IDP based Authentication, limited to Okta
            elif snowflake_authenticator.lower()[:8] == "https://":
                if self.verbose:
                    print(_log_auth_type % "Okta")
                    print(_log_okta_ep % snowflake_authenticator)

                self.conArgs["password"] = snowflake_password
                self.conArgs["authenticator"] = snowflake_authenticator.lower()
            elif snowflake_authenticator.lower() == "snowflake":
                self.conArgs["authenticator"] = default_authenticator
            # if authenticator is not a supported method or the authenticator variable is defined but not specified
            else:
                # defaulting to snowflake as authenticator
                if self.verbose:
                    print(
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
                if self.verbose:
                    print(_log_auth_type % "password")
                self.conArgs["password"] = snowflake_password

            elif os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", ""):
                if self.verbose:
                    print(_log_auth_type % "private key")

                private_key_password = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "")
                if private_key_password:
                    private_key_password = private_key_password.encode()
                else:
                    private_key_password = None
                    if self.verbose:
                        print(_log_pk_enc)
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
        if self.verbose:
            print(SecretManager.global_redact("SQL query: %s" % query))
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


def deploy_command(config):
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
    if len((req_env_var - dict(os.environ).keys())) == len(req_env_var):
        raise ValueError(_err_env_missing)

    # Log some additional details
    if config["dry_run"]:
        print("Running in dry-run mode")
    print(_log_config_details.format(**config))

    # connect to snowflake and maintain connection
    session = SnowflakeSchemachangeSession(config)

    scripts_skipped = 0
    scripts_applied = 0

    # Deal with the change history table (create if specified)
    change_history_table = get_change_history_table_details(
        config["change_history_table"]
    )
    change_history_metadata = session.fetch_change_history_metadata(
        change_history_table
    )
    if change_history_metadata:
        print(
            _log_ch_use.format(
                last_altered=change_history_metadata["last_altered"],
                **change_history_table,
            )
        )
    elif config["create_change_history_table"]:
        # Create the change history table (and containing objects) if it doesn't exist.
        if not config["dry_run"]:
            session.create_change_history_table_if_missing(change_history_table)
        print(_log_ch_create.format(**change_history_table))
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
    print(
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

    # Loop through each script in order and apply any required changes
    for script_name in all_script_names_sorted:
        script = all_scripts[script_name]

        # Apply a versioned-change script only if the version is newer than the most recent change in the database
        # Apply any other scripts, i.e. repeatable scripts, irrespective of the most recent change in the database
        if script_name[0] == "V" and get_alphanum_key(
            script["script_version"]
        ) <= get_alphanum_key(max_published_version):
            if config["verbose"]:
                print(
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
            if (r_scripts_checksum is not None) and script_name in list(
                r_scripts_checksum["script_name"]
            ):
                checksum_last = list(
                    r_scripts_checksum.loc[
                        r_scripts_checksum["script_name"] == script_name, "checksum"
                    ]
                )[0]
            else:
                checksum_last = ""

            # check if there is a change of the checksum in the script
            if checksum_current == checksum_last:
                if config["verbose"]:
                    print(_log_skip_r.format(**script))
                scripts_skipped += 1
                continue

        print(_log_apply.format(**script))
        if not config["dry_run"]:
            session.apply_change_script(script, content, change_history_table)

        scripts_applied += 1

    print(
        _log_apply_set_complete.format(
            scripts_applied=scripts_applied, scripts_skipped=scripts_skipped
        )
    )


def render_command(config, script_path):
    """
    Renders the provided script.

    Note: does not apply secrets filtering.
    """
    # Validate the script file path
    script_path = os.path.abspath(script_path)
    if not os.path.isfile(script_path):
        raise ValueError(f"Invalid script_path folder: {script_path}")
    # Always process with jinja engine
    jinja_processor = JinjaTemplateProcessor(
        project_root=config["root_folder"], modules_folder=config["modules_folder"]
    )
    content = jinja_processor.render(
        jinja_processor.relpath(script_path), config["vars"], config["verbose"]
    )

    checksum = hashlib.sha224(content.encode("utf-8")).hexdigest()
    print("Checksum %s" % checksum)
    print(content)


# This function will return a list containing the parts of the key (split by number parts)
# Each number is converted to and integer and string parts are left as strings
# This will enable correct sorting in python when the lists are compared
# e.g. get_alphanum_key('1.2.2') results in ['', 1, '.', 2, '.', 2, '']
def get_alphanum_key(key):
    def convert(text):
        return int(text) if text.isdigit() else text.lower()

    alphanum_key = [convert(c) for c in re.split("([0-9]+)", key)]
    return alphanum_key


def sorted_alphanumeric(data):
    return sorted(data, key=get_alphanum_key)


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
                if verbose:
                    print(f"Found Versioned file {file_full_path}")
            elif repeatable_script_name_parts is not None:
                script_type = "R"
                if verbose:
                    print(f"Found Repeatable file {file_full_path}")
            elif always_script_name_parts is not None:
                script_type = "A"
                if verbose:
                    print(f"Found Always file {file_full_path}")
            else:
                if verbose:
                    print(f"Ignoring non-change file {file_full_path}")
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


def extract_config_secrets(config: Optional[Dict[str, Any]]) -> Set[str]:
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


def main():
    print("schemachange version: %s" % _schemachange_version)

    args = parse_cli_args(sys.argv[1:])
    cli_config = config_factory(args=args)
    yaml_config = get_yaml_config(
        subcommand=cli_config.subcommand, config_file_path=cli_config.config_file_path
    )

    # set values passed into the cli Overriding values in config file
    merged_config = yaml_config.model_copy(
        update=cli_config.model_dump(
            exclude_unset=False,
            exclude_defaults=False,
            exclude_none=False,
        )
    )
    config = dict()  # TODO: Placeholder

    # set up a secret manager and assign to global scope
    sm = SecretManager()
    SecretManager.set_global_manager(sm)
    # Extract all secrets for --vars
    sm.add_range(extract_config_secrets(config))

    # Then log some details
    print("Using root folder %s" % config["root_folder"])
    if config["modules_folder"]:
        print("Using Jinja modules folder %s" % config["modules_folder"])

    # pretty print the variables in yaml style
    if config["vars"] == {}:
        print("Using variables: {}")
    else:
        print("Using variables:")
        print(
            textwrap.indent(
                SecretManager.global_redact(
                    yaml.dump(config["vars"], sort_keys=False, default_flow_style=False)
                ),
                prefix="  ",
            )
        )

    # Finally, execute the command
    if args.subcommand == "render":
        render_command(config, args.script)
    else:
        deploy_command(config)


if __name__ == "__main__":
    main()
