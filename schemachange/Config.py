from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

_config_file_name = "schemachange-config.yml"


class Config(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    subcommand: Literal["deploy", "render"]
    config_folder: Path = Field(default=".")
    config_file_path: Path | None = None
    root_folder: Path | None = None
    modules_folder: Path | None = None
    vars: dict | None = Field(default_factory=dict)
    verbose: bool = False

    @model_validator(mode="before")
    @classmethod
    def inject_config_file_path(cls, data):
        data["config_file_path"] = Path(data["config_folder"]) / _config_file_name
        return data

    @field_validator("root_folder", "modules_folder")
    @classmethod
    def must_be_valid_dir(cls, v: str) -> str:
        print("hey there!")
        return v


class DeployConfig(Config):
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_role: str | None = None
    snowflake_warehouse: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str | None = None
    change_history_table: str | None = Field(
        default="METADATA.SCHEMACHANGE.CHANGE_HISTORY"
    )
    create_change_history_table: bool = False
    autocommit: bool = False
    dry_run: bool = False
    query_tag: str | None = None
    oauth_config: dict | None = None
    version_number_validation_regex: str | None = None
    raise_exception_on_ignored_versioned_migration: bool = False


class RenderConfig(Config):
    script: str
