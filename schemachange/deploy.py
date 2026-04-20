from __future__ import annotations

import hashlib

import structlog

from schemachange.cli_script_executor import execute_cli_script
from schemachange.CLIScriptExecutionError import CLIScriptExecutionError
from schemachange.config.DeployConfig import DeployConfig
from schemachange.JinjaTemplateProcessor import JinjaTemplateProcessor
from schemachange.session.Script import get_all_scripts_recursively
from schemachange.session.SnowflakeSession import SnowflakeSession
from schemachange.version import get_alphanum_key, sorted_alphanumeric

logger = structlog.getLogger(__name__)


def deploy(config: DeployConfig, session: SnowflakeSession):
    logger.info(
        "Starting deploy",
        dry_run=config.dry_run,
        out_of_order=config.out_of_order,
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
        + sorted_alphanumeric([script for script in all_script_names if script[0] == "r"])
        + sorted_alphanumeric([script for script in all_script_names if script[0] == "a"])
    )

    scripts_skipped = 0
    scripts_applied = 0
    scripts_failed = 0
    failed_scripts: list[str] = []

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
        jinja_processor = JinjaTemplateProcessor(project_root=config.root_folder, modules_folder=config.modules_folder)
        content = jinja_processor.render(
            jinja_processor.relpath(script.file_path),
            config.config_vars,
        )

        checksum_current = hashlib.sha224(content.encode("utf-8")).hexdigest()

        # Apply a versioned-change script based on whether it has been applied and version ordering rules
        if script.type == "V":
            script_metadata = versioned_scripts.get(script.name)

            # First check: Has this script already been applied?
            if script_metadata is not None:
                script_log.debug(
                    "Script has already been applied",
                    max_published_version=max_published_version,
                )
                if script_metadata["checksum"] != checksum_current:
                    script_log.info("Script checksum has drifted since application")
                scripts_skipped += 1
                continue

            # Second check: Version ordering (only if out_of_order is disabled)
            if not config.out_of_order:
                if max_published_version is not None and get_alphanum_key(script.version) <= max_published_version:
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

        # Apply only R scripts where the checksum changed compared to the last execution of snowchange
        if script.type == "R":
            # check if R file was already executed
            if (r_scripts_checksum is not None) and script.name in r_scripts_checksum:
                checksum_last = r_scripts_checksum[script.name][0]
            else:
                checksum_last = ""

            # check if there is a change of the checksum in the script
            if checksum_current == checksum_last:
                script_log.debug("Skipping change script because there is no change since the last execution")
                scripts_skipped += 1
                continue
        should_continue = (script.type == "R" and config.continue_repeatable_on_error) or (
            script.type == "A" and config.continue_always_on_error
        )
        # Determine if this is an out-of-order execution (versioned script with version <= max)
        is_out_of_order = (
            script.type == "V"
            and config.out_of_order
            and max_published_version is not None
            and get_alphanum_key(script.version) <= max_published_version
        )
        try:
            # Prepare content for execution (apply trailing comment fix)
            # This is done AFTER checksum computation to maintain checksum stability (issue #414)
            executable_content = jinja_processor.prepare_for_execution(
                content,
                jinja_processor.relpath(script.file_path),
            )

            # Execute the script based on its format (SQL or CLI)
            if script.format == "CLI":
                # Execute CLI script via subprocess
                try:
                    execution_time = execute_cli_script(
                        script=script,
                        content=executable_content,
                        root_folder=config.root_folder,
                        dry_run=config.dry_run,
                        log=script_log,
                        out_of_order=is_out_of_order,
                    )

                    # Record successful execution in change history (unless dry run)
                    if not config.dry_run:
                        session.record_change_history(
                            script=script,
                            checksum=checksum_current,
                            execution_time=execution_time,
                            status="Success",
                            logger=script_log,
                        )
                except CLIScriptExecutionError as e:
                    # Record failed execution in change history (unless dry run)
                    if not config.dry_run:
                        session.record_change_history(
                            script=script,
                            checksum=checksum_current,
                            execution_time=getattr(e, "execution_time", 0),
                            status="Failed",
                            error_message=str(e),
                            logger=script_log,
                        )
                    raise  # Re-raise the exception after recording
            else:
                # Execute SQL script via Snowflake session
                session.apply_change_script(
                    script=script,
                    script_content=executable_content,
                    dry_run=config.dry_run,
                    logger=script_log,
                    out_of_order=is_out_of_order,
                )

            scripts_applied += 1
        except Exception as e:
            scripts_failed += 1
            failed_scripts.append(script.name)
            script_log.error("Failed to apply change script", error=str(e))
            if not should_continue:
                raise

    if scripts_failed > 0:
        logger.error(
            "Completed with errors",
            scripts_applied=scripts_applied,
            scripts_skipped=scripts_skipped,
            scripts_failed=scripts_failed,
            failed_scripts=failed_scripts,
        )
        raise Exception(f"{scripts_failed} change script(s) failed: {', '.join(failed_scripts)}")

    logger.info(
        "Completed successfully",
        scripts_applied=scripts_applied,
        scripts_skipped=scripts_skipped,
    )
