"""Exercise checksum policy through the real CLI/environment/YAML merge path."""

import os
import sys
from unittest import mock

import pytest
import structlog
import yaml

from schemachange.config.ChecksumChangedAction import ChecksumChangedAction
from schemachange.config.get_merged_config import get_merged_config
from schemachange.config.parse_cli_args import parse_cli_args


@pytest.fixture
def load_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with mock.patch.dict(os.environ, {}, clear=True):

        def load(
            yaml_action=None, env_action=None, cli_action=None, config_version=2, flag="--checksum-changed-action"
        ):
            config = {} if yaml_action is None else {"checksum-changed-action": yaml_action}
            if config_version == 2:
                config = {"config-version": 2, "schemachange": config}
            (tmp_path / "schemachange-config.yml").write_text(yaml.safe_dump(config), encoding="utf-8")
            os.environ.pop("SCHEMACHANGE_CHECKSUM_CHANGED_ACTION", None)
            if env_action is not None:
                os.environ["SCHEMACHANGE_CHECKSUM_CHANGED_ACTION"] = env_action
            args = ["schemachange", "deploy"]
            if cli_action is not None:
                args.extend([flag, cli_action])
            monkeypatch.setattr(sys, "argv", args)
            return get_merged_config(logger=structlog.get_logger())

        yield load


@pytest.mark.parametrize("source", ["yaml", "env", "cli"])
@pytest.mark.parametrize("action", list(ChecksumChangedAction))
def test_all_configuration_sources(load_config, source, action):
    config = load_config(**{f"{source}_action": action.value})
    assert config.checksum_changed_action is action


@pytest.mark.parametrize("config_version", [1, 2])
@pytest.mark.parametrize("action", list(ChecksumChangedAction))
def test_yaml_versions_and_case_insensitivity(load_config, config_version, action):
    config = load_config(yaml_action=action.value.lower(), config_version=config_version)
    assert config.checksum_changed_action is action


@pytest.mark.parametrize("action", list(ChecksumChangedAction))
def test_environment_case_insensitivity(load_config, action):
    assert load_config(env_action=action.value.lower()).checksum_changed_action is action


@pytest.mark.parametrize(
    "yaml_action,env_action,cli_action,expected",
    [
        (None, None, None, "IGNORE"),
        ("EXECUTE", None, None, "EXECUTE"),
        ("EXECUTE", "ERROR", None, "ERROR"),
        ("EXECUTE", "ERROR", "IGNORE", "IGNORE"),
        ("ERROR", "IGNORE", None, "IGNORE"),
    ],
)
def test_precedence(load_config, yaml_action, env_action, cli_action, expected):
    config = load_config(yaml_action, env_action, cli_action)
    assert config.checksum_changed_action is ChecksumChangedAction(expected)


def test_prefixed_cli_alias(load_config):
    assert (
        load_config(cli_action="ERROR", flag="--schemachange-checksum-changed-action").checksum_changed_action
        is ChecksumChangedAction.ERROR
    )


@pytest.mark.parametrize("value", ["INVALID", "", False, 42, ["ERROR"], {"action": "ERROR"}])
def test_invalid_yaml_values(load_config, value):
    with pytest.raises(ValueError, match="Invalid checksum-changed-action.*IGNORE, ERROR, EXECUTE"):
        load_config(yaml_action=value)


@pytest.mark.parametrize("value", ["INVALID", ""])
def test_invalid_environment_values(load_config, value):
    with pytest.raises(ValueError, match="SCHEMACHANGE_CHECKSUM_CHANGED_ACTION.*IGNORE, ERROR, EXECUTE"):
        load_config(env_action=value)


def test_invalid_cli_value(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_cli_args(["deploy", "--checksum-changed-action", "INVALID"])
    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
