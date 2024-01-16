import hashlib
import os
import re
import sys
import textwrap
import yaml

from schemachange.SnowflakeSchemachangeSession import SnowflakeSchemachangeSession
from schemachange.get_all_scripts_recursively import get_all_scripts_recursively
from schemachange.render import render
from schemachange.extract_config_secrets import extract_config_secrets
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
_err_invalid_cht = "Invalid change history table name: %s"
_log_okta_ep = "Okta Endpoint: %s"
CONFIG_DEFAULTS = {}  # TODO: Placeholder to allow test cases to run
# endregion Global Variables


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


def main():
    print("schemachange version: %s" % _schemachange_version)

    args = parse_cli_args(sys.argv[1:])
    cli_config = config_factory(args=args)
    yaml_config = get_yaml_config(
        subcommand=cli_config.subcommand,
        config_file_path=cli_config.config_file_path,
        script_path=getattr(cli_config, "script_path", None),
    )

    # override the YAML config with the CLI configuration
    config = yaml_config.merge_exclude_unset(other=cli_config)

    # set up a secret manager and assign to global scope
    sm = SecretManager()
    SecretManager.set_global_manager(sm)
    # Extract all secrets for --vars
    sm.add_range(extract_config_secrets(config))

    # Then log some details
    print(f"Using root folder {str(config.root_folder)}")
    if config.modules_folder:
        print(f"Using Jinja modules folder {str(config.modules_folder)}")

    # pretty print the variables in yaml style
    if not config.vars:
        print("Using variables: {}")
    else:
        print("Using variables:")
        print(
            textwrap.indent(
                SecretManager.global_redact(
                    yaml.dump(config.vars, sort_keys=False, default_flow_style=False)
                ),
                prefix="  ",
            )
        )

    # Finally, execute the command
    if config.subcommand == "render":
        render(config=config, script_path=config.script_path)
    else:
        deploy_command(config=config)


if __name__ == "__main__":
    main()
