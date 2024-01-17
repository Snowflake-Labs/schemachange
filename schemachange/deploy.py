import hashlib
import re

from schemachange.Config import DeployConfig
from schemachange.session.SnowflakeSession import SnowflakeSession
from schemachange.get_all_scripts_recursively import get_all_scripts_recursively
from schemachange.JinjaTemplateProcessor import JinjaTemplateProcessor


_metadata_database_name = "METADATA"
_metadata_schema_name = "SCHEMACHANGE"
_metadata_table_name = "CHANGE_HISTORY"


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
            raise ValueError(
                f"Invalid change history table name: {change_history_table}"
            )
    # if the object name does not include '"' raise to upper case on return
    return {k: v if '"' in v else v.upper() for (k, v) in details.items()}


def deploy(config: DeployConfig, session: SnowflakeSession):
    if config.dry_run:
        print("Running in dry-run mode")
    print(
        f"Using Snowflake account {session.account}\n"
        f"Using default role {session.role}\n"
        f"Using default warehouse {session.warehouse}\n"
        f"Using default database {session.database} schema {session.schema}"
    )

    scripts_skipped = 0
    scripts_applied = 0

    # Deal with the change history table (create if specified)
    change_history_table = get_change_history_table_details(config.change_history_table)
    change_history_metadata = session.fetch_change_history_metadata(
        change_history_table
    )
    if change_history_metadata:
        print(
            f"Using change history table {database_name}.{schema_name}.{table_name} "
            f"(last altered {change_history_metadata['last_altered']})"
        )
    elif config["create_change_history_table"]:
        # Create the change history table (and containing objects) if it doesn't exist.
        if not config["dry_run"]:
            session.create_change_history_table_if_missing(change_history_table)
        print(
            f"Created change history table {database_name}.{schema_name}.{table_name}"
        )
    else:
        raise ValueError(
            f"Unable to find change history table {database_name}.{schema_name}.{table_name}"
        )

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
    print(f"Max applied change script version: {max_published_version_display}")

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
                    f"Skipping change script {script_name} because it's older "
                    f"than the most recently applied change ({max_published_version})"
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
                    print(
                        f"Skipping change script {script_name} because there is no change since the last execution"
                    )
                scripts_skipped += 1
                continue

        print(f"Applying change script {script_name}")
        if not config["dry_run"]:
            session.apply_change_script(script, content, change_history_table)

        scripts_applied += 1

    print(
        f"Successfully applied {scripts_applied} change scripts "
        f"(skipping {scripts_skipped}) \nCompleted successfully"
    )
