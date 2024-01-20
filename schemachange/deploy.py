import hashlib
import re

import structlog

from schemachange.Config import DeployConfig
from schemachange.JinjaTemplateProcessor import JinjaTemplateProcessor
from schemachange.session.Script import get_all_scripts_recursively
from schemachange.session.SnowflakeSession import SnowflakeSession

logger = structlog.getLogger(__name__)
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
    log = logger.bind(
        snowflake_account=session.account,
        default_role=session.role,
        default_warehouse=session.warehouse,
        default_database=session.database,
        default_schema=session.schema,
        change_history_table=session.change_history_table.fully_qualified,
    )

    log.info(
        "starting deploy",
    )

    # Deal with the change history table (create if specified)
    change_history_metadata = session.fetch_change_history_metadata()
    if change_history_metadata:
        log.info(
            "Using existing change history table",
            {"last_altered": change_history_metadata["last_altered"]},
        )
    elif config.create_change_history_table:
        # Create the change history table (and containing objects) if it doesn't exist.
        session.create_change_history_table_if_missing()
        logger.info("Created change history table")
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

    log.info(
        "Max applied change script version %(max_published_version)s"
        % {
            "max_published_version": max_published_version
            if max_published_version != ""
            else "None"
        }
    )

    # Find all scripts in the root folder (recursively) and sort them correctly
    all_scripts = get_all_scripts_recursively(
        root_directory=config.root_folder,
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
        script_log = log.bind(
            script_name=script.name,
            script_type=script.type,
            script_version=getattr(script, "version", "N/A"),
        )

        # Apply a versioned-change script only if the version is newer than the most recent change in the database
        # Apply any other scripts, i.e. repeatable scripts, irrespective of the most recent change in the database
        if script.type == "V" and get_alphanum_key(script.version) <= get_alphanum_key(
            max_published_version
        ):
            script_log.debug(
                "Skipping change script because it's older than the most recently applied change",
                max_published_version=max_published_version,
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
                script_log.debug(
                    "Skipping change script because there is no change since the last execution"
                )
                scripts_skipped += 1
                continue

        session.apply_change_script(script, content)

        scripts_applied += 1

    log.info(
        "Completed successfully",
        scripts_applied=scripts_applied,
        scripts_skipped=scripts_skipped,
    )
