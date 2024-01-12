from __future__ import annotations

from pathlib import Path
from typing import Literal, ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic_core.core_schema import ValidationInfo


class Config(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    default_config_file_name: ClassVar[str] = "schemachange-config.yml"

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
        config_folder = data.get("config_folder")
        if config_folder is None:
            config_folder = "."

        data["config_file_path"] = Path(config_folder) / cls.default_config_file_name
        return data

    @field_validator("config_folder", "root_folder", "modules_folder")
    @classmethod
    def must_be_valid_dir(cls, v: Path, info: ValidationInfo) -> Path:
        if not v.is_dir():
            print("Hey there!")
            raise ValueError(f"Invalid {info.field_name} folder: {v}")
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
