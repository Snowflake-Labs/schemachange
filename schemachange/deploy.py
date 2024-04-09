from __future__ import annotations

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

    if key is None:
        return ""

    alphanum_key = [convert(c) for c in re.split("([0-9]+)", key)]
    return alphanum_key


def sorted_alphanumeric(data):
    return sorted(data, key=get_alphanum_key)


def deploy(config: DeployConfig, session: SnowflakeSession):
    logger.info(
        "starting deploy",
        snowflake_account=session.account,
        default_role=session.role,
        default_warehouse=session.warehouse,
        default_database=session.database,
        default_schema=session.schema,
        change_history_table=session.change_history_table.fully_qualified,
    )

    (
        versioned_scripts,
        r_scripts_checksum,
        max_published_version,
    ) = session.get_script_metadata(
        create_change_history_table=config.create_change_history_table,
        dry_run=config.dry_run,
    )

    max_published_version = get_alphanum_key(max_published_version)

    # Find all scripts in the root folder (recursively) and sort them correctly
    all_scripts = get_all_scripts_recursively(
        root_directory=config.root_folder,
        version_number_regex=config.version_number_validation_regex,
    )
    all_script_names = list(all_scripts.keys())
    # Sort scripts such that versioned scripts get applied first and then the repeatable ones.
    all_script_names_sorted = (
        sorted_alphanumeric([script for script in all_script_names if script[0] == "v"])
        + sorted_alphanumeric(
            [script for script in all_script_names if script[0] == "r"]
        )
        + sorted_alphanumeric(
            [script for script in all_script_names if script[0] == "a"]
        )
    )

    scripts_skipped = 0
    scripts_applied = 0

    # Loop through each script in order and apply any required changes
    for script_name in all_script_names_sorted:
        script = all_scripts[script_name]
        script_log = logger.bind(
            # The logging keys will be sorted alphabetically.
            # Appending 'a' is a lazy way to get the script name to appear at the start of the log
            a_script_name=script.name,
            script_version=getattr(script, "version", "N/A"),
        )
        # Always process with jinja engine
        jinja_processor = JinjaTemplateProcessor(
            project_root=config.root_folder, modules_folder=config.modules_folder
        )
        content = jinja_processor.render(
            jinja_processor.relpath(script.file_path),
            config.vars,
        )

        checksum_current = hashlib.sha224(content.encode("utf-8")).hexdigest()

        # Apply a versioned-change script only if the version is newer than the most recent change in the database
        # Apply any other scripts, i.e. repeatable scripts, irrespective of the most recent change in the database
        if script.type == "V":
            script_metadata = versioned_scripts.get(script.name)

            if (
                max_published_version != ""
                and get_alphanum_key(script.version) <= max_published_version
            ):
                if script_metadata is None:
                    if config.raise_exception_on_ignored_versioned_script:
                        raise ValueError(
                            f"Versioned script will never be applied: {script.name}\n"
                            f"Version number is less than the max version number: {max_published_version}"
                        )
                    else:
                        script_log.debug(
                            "Skipping versioned script because it's older than the most recently applied change",
                            max_published_version=max_published_version,
                        )
                        scripts_skipped += 1
                        continue
                else:
                    script_log.debug(
                        "Script has already been applied",
                        max_published_version=str(max_published_version),
                    )
                    if script_metadata["checksum"] != checksum_current:
                        script_log.info("Script checksum has drifted since application")

                    scripts_skipped += 1
                    continue

        # Apply only R scripts where the checksum changed compared to the last execution of snowchange
        if script.type == "R":
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

        session.apply_change_script(
            script=script,
            script_content=content,
            dry_run=config.dry_run,
            logger=script_log,
        )

        scripts_applied += 1

    logger.info(
        "Completed successfully",
        scripts_applied=scripts_applied,
        scripts_skipped=scripts_skipped,
    )
