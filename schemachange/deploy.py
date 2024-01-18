import hashlib
import re

from schemachange.Config import DeployConfig
from schemachange.session.SnowflakeSession import SnowflakeSession
from schemachange.session.Script import get_all_scripts_recursively
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


def deploy(config: DeployConfig, session: SnowflakeSession):
    print(
        f"Using Snowflake account {session.account}\n"
        f"Using default role {session.role}\n"
        f"Using default warehouse {session.warehouse}\n"
        f"Using default database {session.database} schema {session.schema}"
    )

    # Deal with the change history table (create if specified)
    change_history_metadata = session.fetch_change_history_metadata()
    if change_history_metadata:
        print(
            f"Using change history table {session.change_history_table.fully_qualified} "
            f"(last altered {change_history_metadata['last_altered']})"
        )
    elif config.create_change_history_table:
        # Create the change history table (and containing objects) if it doesn't exist.
        session.create_change_history_table_if_missing()
        print(
            f"Created change history table {session.change_history_table.fully_qualified}"
        )
    else:
        raise ValueError(
            f"Unable to find change history table {session.change_history_table.fully_qualified}"
        )

    # Find the max published version
    max_published_version = ""

    change_history = None
    r_scripts_checksum = None
    if (config["dry_run"] and change_history_metadata) or not config["dry_run"]:
        change_history = session.fetch_versioned_scripts()
        r_scripts_checksum = session.fetch_repeatable_scripts()

    if change_history:
        max_published_version = change_history[0]

    print(
        f"Max applied change script version: {max_published_version if max_published_version != '' else 'None'}"
    )

    # Find all scripts in the root folder (recursively) and sort them correctly
    all_scripts = get_all_scripts_recursively(
        root_directory=config.root_folder,
        verbose=config.verbose,
        version_number_regex=config.version_number_validation_regex,
    )
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

    scripts_skipped = 0
    scripts_applied = 0

    # Loop through each script in order and apply any required changes
    for script_name in all_script_names_sorted:
        script = all_scripts[script_name]

        # Apply a versioned-change script only if the version is newer than the most recent change in the database
        # Apply any other scripts, i.e. repeatable scripts, irrespective of the most recent change in the database
        if script.type == "V" and get_alphanum_key(script.version) <= get_alphanum_key(
            max_published_version
        ):
            if config.verbose:
                print(
                    f"Skipping change script {script.name} because it's older "
                    f"than the most recently applied change ({max_published_version})"
                )
            scripts_skipped += 1
            continue

        # Always process with jinja engine
        jinja_processor = JinjaTemplateProcessor(
            project_root=config.root_folder, modules_folder=config.modules_folder
        )
        content = jinja_processor.render(
            jinja_processor.relpath(script.file_path),
            config.vars,
            config.verbose,
        )

        # Apply only R scripts where the checksum changed compared to the last execution of snowchange
        if script.type == "R":
            # Compute the checksum for the script
            checksum_current = hashlib.sha224(content.encode("utf-8")).hexdigest()

            # check if R file was already executed
            if (r_scripts_checksum is not None) and script.name in r_scripts_checksum:
                checksum_last = r_scripts_checksum[script.name][0]
            else:
                checksum_last = ""

            # check if there is a change of the checksum in the script
            if checksum_current == checksum_last:
                if config.verbose:
                    print(
                        f"Skipping change script {script.name} because there is no change since the last execution"
                    )
                scripts_skipped += 1
                continue

        session.apply_change_script(script, content)

        scripts_applied += 1

    print(
        f"Successfully applied {scripts_applied} change scripts "
        f"(skipping {scripts_skipped}) \nCompleted successfully"
    )
