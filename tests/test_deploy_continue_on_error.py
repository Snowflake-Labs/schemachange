from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.DeployConfig import DeployConfig
from schemachange.deploy import deploy
from schemachange.session.SnowflakeSession import SnowflakeSession


def test_deploy_continues_on_error(tmp_path: Path):
    (tmp_path / "V1__one.sql").write_text("select 1;")
    (tmp_path / "V2__two.sql").write_text("select 1;")
    config = DeployConfig.factory(
        config_file_path=tmp_path / "config.yml",
        root_folder=tmp_path,
        continue_versioned_on_error=True,
    )

    session = mock.create_autospec(SnowflakeSession, instance=True)
    session.account = "acct"
    session.role = "role"
    session.warehouse = "wh"
    session.database = "db"
    session.schema = "sc"
    session.change_history_table = ChangeHistoryTable()
    session.get_script_metadata.return_value = ({}, {}, None)
    session.apply_change_script.side_effect = [Exception("boom"), None]

    with pytest.raises(Exception) as excinfo:
        deploy(config, session)
    assert "V1__one.sql" in str(excinfo.value)

    assert [
        call.kwargs["script"].name
        for call in session.apply_change_script.call_args_list
    ] == ["V1__one.sql", "V2__two.sql"]
