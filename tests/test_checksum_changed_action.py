"""Checksum policy tests using real script discovery and Jinja rendering."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from dataclasses import replace
from types import SimpleNamespace
from unittest import mock

import pytest
from structlog.testing import capture_logs

from schemachange.ChecksumChangedError import ChecksumChangedError
from schemachange.CLIScriptExecutionError import CLIScriptExecutionError
from schemachange.config.ChecksumChangedAction import ChecksumChangedAction
from schemachange.config.DeployConfig import DeployConfig
from schemachange.deploy import deploy
from schemachange.JinjaTemplateProcessor import JinjaTemplateProcessor
from schemachange.ScriptExecutionError import ScriptExecutionError
from schemachange.session.SnowflakeSession import SnowflakeSession


@pytest.fixture(params=["sql", "cli.yml"])
def migration(tmp_path, request):
    path = tmp_path / f"V1.2.0__example.{request.param}"
    content = (
        "SELECT {{ value }};"
        if request.param == "sql"
        else 'steps:\n  - cli: snow\n    command: sql\n    args: ["-q", "SELECT {{ value }}"]\n'
    )
    path.write_text(content, encoding="utf-8")
    processor = JinjaTemplateProcessor(project_root=tmp_path)
    checksums = [
        hashlib.sha224(processor.render(path.name, {"value": value}).encode("utf-8")).hexdigest() for value in (1, 2)
    ]
    return SimpleNamespace(
        path=path,
        old_checksum=checksums[0],
        current_checksum=checksums[1],
        config=DeployConfig(root_folder=tmp_path, config_vars={"value": 2}),
        format=request.param,
    )


@pytest.fixture
def session():
    session = mock.MagicMock(spec=SnowflakeSession)
    session.account = "test_account"
    session.role = "test_role"
    session.warehouse = "test_warehouse"
    session.database = "test_database"
    session.schema = "test_schema"
    session.logger = mock.Mock()
    session.change_history_table = mock.Mock(fully_qualified="DB.SCHEMA.CHANGE_HISTORY")
    return session


@pytest.fixture
def cli_executor():
    with mock.patch("schemachange.deploy.execute_cli_script", return_value=0.1) as executor:
        yield executor


@pytest.mark.parametrize("action", list(ChecksumChangedAction))
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    "applied,max_version,out_of_order,changed,ignore,error,execute",
    [
        pytest.param(False, "1.1.0", False, False, "apply", "apply", "apply", id="row-1"),
        pytest.param(False, "1.1.0", True, False, "apply", "apply", "apply", id="row-2"),
        pytest.param(False, "1.3.0", False, False, "skip", "skip", "skip", id="row-3"),
        pytest.param(False, "1.3.0", True, False, "apply", "apply", "apply", id="row-4"),
        pytest.param(True, "1.1.0", False, False, "skip", "skip", "skip", id="row-5"),
        pytest.param(True, "1.1.0", False, True, "skip", "error", "apply", id="row-6"),
        pytest.param(True, "1.1.0", True, False, "skip", "skip", "skip", id="row-7"),
        pytest.param(True, "1.1.0", True, True, "skip", "error", "apply", id="row-8"),
        pytest.param(True, "1.3.0", False, False, "skip", "skip", "skip", id="row-9"),
        pytest.param(True, "1.3.0", False, True, "skip", "error", "skip", id="row-10"),
        pytest.param(True, "1.3.0", True, False, "skip", "skip", "skip", id="row-11"),
        pytest.param(True, "1.3.0", True, True, "skip", "error", "apply", id="row-12"),
    ],
)
def test_versioned_decision_matrix(
    migration,
    session,
    cli_executor,
    action,
    dry_run,
    applied,
    max_version,
    out_of_order,
    changed,
    ignore,
    error,
    execute,
):
    """The twelve rows proposed in #349, with row 10 following the recommendation to skip."""
    checksum = migration.old_checksum if changed else migration.current_checksum
    history = {migration.path.name: {"checksum": checksum}} if applied else {}
    session.get_script_metadata.return_value = (history, {}, max_version)
    config = replace(migration.config, checksum_changed_action=action, out_of_order=out_of_order, dry_run=dry_run)
    expected = {"IGNORE": ignore, "ERROR": error, "EXECUTE": execute}[action.value]

    if expected == "error":
        with pytest.raises(ChecksumChangedError) as exc:
            deploy(config, session)
        assert migration.path.name in str(exc.value)
        assert migration.old_checksum in str(exc.value)
        assert migration.current_checksum in str(exc.value)
        assert "new versioned script" in str(exc.value)
    else:
        deploy(config, session)

    if expected != "apply":
        session.apply_change_script.assert_not_called()
        cli_executor.assert_not_called()
        session.record_change_history.assert_not_called()
    elif migration.format == "sql":
        session.apply_change_script.assert_called_once()
        kwargs = session.apply_change_script.call_args.kwargs
        assert kwargs["checksum"] == migration.current_checksum
        assert kwargs["dry_run"] is dry_run
        assert kwargs["out_of_order"] is (out_of_order and max_version == "1.3.0")
        cli_executor.assert_not_called()
    else:
        cli_executor.assert_called_once()
        assert cli_executor.call_args.kwargs["dry_run"] is dry_run
        assert cli_executor.call_args.kwargs["out_of_order"] is (out_of_order and max_version == "1.3.0")
        session.apply_change_script.assert_not_called()
        if dry_run:
            session.record_change_history.assert_not_called()
        else:
            session.record_change_history.assert_called_once()
            assert session.record_change_history.call_args.kwargs["checksum"] == migration.current_checksum
            assert session.record_change_history.call_args.kwargs["status"] == "Success"


@pytest.mark.parametrize("dry_run", [False, True])
def test_default_preserves_drift_log_and_skips(migration, session, cli_executor, dry_run):
    session.get_script_metadata.return_value = (
        {migration.path.name: {"checksum": migration.old_checksum}},
        {},
        "1.2.0",
    )
    with capture_logs() as logs:
        deploy(replace(migration.config, dry_run=dry_run), session)
    assert any(
        log["event"] == "Script checksum has drifted since application" and log["log_level"] == "info" for log in logs
    )
    session.apply_change_script.assert_not_called()
    cli_executor.assert_not_called()


@pytest.mark.parametrize("applied", [False, True])
@pytest.mark.parametrize("action", list(ChecksumChangedAction))
def test_ignored_version_flag_only_errors_for_new_scripts(migration, session, cli_executor, applied, action):
    """A script equal to the maximum version is also subject to ordering rules."""
    history = {migration.path.name: {"checksum": migration.old_checksum}} if applied else {}
    session.get_script_metadata.return_value = (history, {}, "1.2.0")
    config = replace(migration.config, checksum_changed_action=action, raise_exception_on_ignored_versioned_script=True)
    if not applied:
        with pytest.raises(ValueError, match="Versioned script will never be applied"):
            deploy(config, session)
    elif action == ChecksumChangedAction.ERROR:
        with pytest.raises(ChecksumChangedError):
            deploy(config, session)
    else:
        with capture_logs() as logs:
            deploy(config, session)
        if action == ChecksumChangedAction.EXECUTE:
            assert any("re-execution requires --out-of-order" in log["event"] for log in logs)
    session.apply_change_script.assert_not_called()
    cli_executor.assert_not_called()


@pytest.mark.parametrize("action", list(ChecksumChangedAction))
def test_first_deploy_without_history(migration, session, cli_executor, action):
    session.get_script_metadata.return_value = ({}, {}, None)
    deploy(replace(migration.config, checksum_changed_action=action), session)
    assert session.apply_change_script.call_count + cli_executor.call_count == 1


@pytest.mark.parametrize("action", list(ChecksumChangedAction))
@pytest.mark.parametrize("prefix,changed,should_run", [("R", False, False), ("R", True, True), ("A", False, True)])
def test_repeatable_and_always_scripts_are_unaffected(
    migration, session, cli_executor, action, prefix, changed, should_run
):
    path = migration.path.rename(migration.path.with_name(f"{prefix}__example.{migration.format}"))
    checksum = migration.old_checksum if changed else migration.current_checksum
    session.get_script_metadata.return_value = ({}, {path.name: [checksum]}, "1.2.0")
    deploy(replace(migration.config, checksum_changed_action=action), session)
    assert session.apply_change_script.call_count + cli_executor.call_count == int(should_run)


def test_successful_reexecution_is_not_repeated(migration, session, cli_executor):
    """Use the real history reader to check the next deploy sees the new checksum."""
    rows = [("1.2.0", migration.path.name, migration.old_checksum)]
    session.execute_snowflake_query.return_value = [rows]

    def get_metadata(**kwargs):
        history, maximum = SnowflakeSession.fetch_versioned_scripts(session)
        return history, {}, maximum

    def record_success(**kwargs):
        rows.insert(0, ("1.2.0", kwargs["script"].name, kwargs["checksum"]))

    session.get_script_metadata.side_effect = get_metadata
    session.apply_change_script.side_effect = record_success
    session.record_change_history.side_effect = record_success
    config = replace(migration.config, checksum_changed_action=ChecksumChangedAction.EXECUTE, out_of_order=True)

    deploy(config, session)
    assert len(rows) == 2
    session.apply_change_script.reset_mock()
    session.record_change_history.reset_mock()
    cli_executor.reset_mock()

    deploy(config, session)
    session.apply_change_script.assert_not_called()
    session.record_change_history.assert_not_called()
    cli_executor.assert_not_called()


def test_execute_dry_run_reports_intent(migration, session, cli_executor):
    session.get_script_metadata.return_value = (
        {migration.path.name: {"checksum": migration.old_checksum}},
        {},
        "1.2.0",
    )
    config = replace(
        migration.config, checksum_changed_action=ChecksumChangedAction.EXECUTE, out_of_order=True, dry_run=True
    )
    with capture_logs() as logs:
        deploy(config, session)
    assert any("would re-execute" in log["event"] for log in logs)
    session.record_change_history.assert_not_called()


def test_reexecution_failure_stops_deployment(migration, session, cli_executor):
    session.get_script_metadata.return_value = (
        {migration.path.name: {"checksum": migration.old_checksum}},
        {},
        "1.2.0",
    )
    # A later script must not run after a failed re-execution.
    migration.path.with_name(f"V1.3.0__later.{migration.format}").write_text(
        migration.path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    error_type = ScriptExecutionError if migration.format == "sql" else CLIScriptExecutionError
    error = error_type(migration.path.name, migration.path, "V", "execution failed")
    executor = session.apply_change_script if migration.format == "sql" else cli_executor
    executor.side_effect = error
    config = replace(migration.config, checksum_changed_action=ChecksumChangedAction.EXECUTE, out_of_order=True)
    with pytest.raises(error_type):
        deploy(config, session)
    executor.assert_called_once()
    if migration.format == "cli.yml":
        session.record_change_history.assert_called_once()
        assert session.record_change_history.call_args.kwargs["status"] == "Failed"


@pytest.mark.parametrize("action,exit_code", [("IGNORE", 0), ("ERROR", 1)])
@pytest.mark.parametrize("dry_run", [False, True])
def test_cli_process_exit_and_recovery_message(migration, action, exit_code, dry_run):
    """Run the real CLI in a child process, mocking only the database session."""
    program = f"""
from unittest import mock
from schemachange.cli import main
with mock.patch('schemachange.cli.SnowflakeSession') as session_class:
    session = session_class.return_value
    session.get_script_metadata.return_value = (
        {{{migration.path.name!r}: {{'checksum': {migration.old_checksum!r}}}}}, {{}}, '1.2.0'
    )
    try:
        main()
    finally:
        session.apply_change_script.assert_not_called()
        session.record_change_history.assert_not_called()
"""
    args = [
        sys.executable,
        "-c",
        program,
        "deploy",
        "--root-folder",
        str(migration.path.parent),
        "--config-folder",
        str(migration.path.parent),
        "--vars",
        '{"value": 2}',
        "--checksum-changed-action",
        action,
    ]
    if dry_run:
        args.append("--dry-run")
    env = {key: value for key, value in os.environ.items() if not key.startswith(("SCHEMACHANGE_", "SNOWFLAKE_"))}
    result = subprocess.run(args, capture_output=True, text=True, env=env, timeout=30)
    output = result.stdout + result.stderr
    assert result.returncode == exit_code, output
    if action == "ERROR":
        assert migration.path.name in output
        assert "Restore the applied script and its rendering inputs" in output
        assert "new versioned script" in output
        assert "Configuration error" not in output
        assert "schemachange verify" not in output
        assert "Completed successfully" not in output
    else:
        assert "Script checksum has drifted since application" in output
        assert "Completed successfully" in output
