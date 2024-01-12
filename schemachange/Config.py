from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

_config_file_name = "schemachange-config.yml"


@dataclass(kw_only=True, frozen=True)
class Config:
    subcommand: Literal["deploy", "render"]
    config_folder: str = field(default=".")
    config_file_path: str
    root_folder: str | None = None
    modules_folder: str | None = None
    vars: dict | None = None
    verbose: bool = False

    @classmethod
    def factory(cls, **kwargs):
        kwargs["config_file_path"] = Path(kwargs["config_folder"]) / _config_file_name

        return cls(
            **{
                k: v
                for k, v in kwargs.items()
                if k in inspect.signature(cls).parameters
            }
        )


@dataclass(kw_only=True, frozen=True)
class DeployConfig(Config):
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_role: str | None = None
    snowflake_warehouse: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str | None = None
    change_history_table: str = field(default="METADATA.SCHEMACHANGE.CHANGE_HISTORY")
    create_change_history_table: bool = False
    autocommit: bool = False
    dry_run: bool = False
    query_tag: str | None = None
    oauth_config: dict | None = None
    version_number_validation_regex: str | None = None
    raise_exception_on_ignored_versioned_migration: bool = False


@dataclass(kw_only=True, frozen=True)
class RenderConfig(Config):
    script: str
