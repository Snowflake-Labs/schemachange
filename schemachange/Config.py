from __future__ import annotations

from abc import ABC
from argparse import Namespace
from pathlib import Path
from typing import Literal, ClassVar, TypeVar

import structlog
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic_core.core_schema import ValidationInfo

from schemachange.SecretManager import SecretManager

logger = structlog.getLogger(__name__)
T = TypeVar("T", bound="Config")


class Config(BaseModel, ABC):
    model_config = ConfigDict(frozen=True, extra="ignore")
    default_config_file_name: ClassVar[str] = "schemachange-config.yml"

    subcommand: Literal["deploy", "render"]
    config_folder: Path = Field(default=Path("."))
    config_file_path: Path | None = None
    root_folder: Path | None = Field(default=Path("."))
    modules_folder: Path | None = None
    vars: dict | None = Field(default_factory=dict)

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
    def must_be_valid_dir(cls, v: Path, info: ValidationInfo) -> Path | None:
        if v is None:
            return v
        if not v.is_dir():
            raise ValueError(f"Invalid {info.field_name} folder: {str(v)}")
        return v

    @field_validator("vars", mode="before")
    @classmethod
    def must_be_dict(cls, v: str | dict) -> dict:
        if v is None:
            return {}

        if not isinstance(v, dict):
            raise ValueError(
                "vars did not parse correctly, please check its configuration"
            )

        if "schemachange" in v.keys():
            raise ValueError(
                "The variable 'schemachange' has been reserved for use by schemachange, please use a different name"
            )

        return v

    def merge_exclude_unset(self: T, other: T) -> T:
        other_kwargs = other.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )
        other_kwargs.pop("config_file_path")
        if "change_history_table" in other_kwargs:
            other_kwargs["change_history_table"] = other.change_history_table

        return self.model_copy(update=other_kwargs)

    def log_details(self, secret_manager: SecretManager):
        logger.info("Using root folder", root_folder=self.root_folder)
        if self.modules_folder:
            logger.info(
                "Using Jinja modules folder", modules_folder=str(self.modules_folder)
            )

        if not self.vars:
            logger.info("No variables set")
        else:
            logger.info(
                "Using variables", **self.vars
            )  # TODO: Confirm secret redaction


class Table(BaseModel):
    # model_config = ConfigDict(frozen=True, extra="ignore")

    table_name: str = "CHANGE_HISTORY"
    schema_name: str = "SCHEMACHANGE"
    database_name: str = "METADATA"

    @property
    def fully_qualified(self) -> str:
        return f"{self.database_name}.{self.schema_name}.{self.table_name}"

    @classmethod
    def from_str(cls, v: str):
        details = dict()
        table_name_parts = v.strip().split(".")
        if len(table_name_parts) == 1:
            details["table_name"] = table_name_parts[0]
        elif len(table_name_parts) == 2:
            details["table_name"] = table_name_parts[1]
            details["schema_name"] = table_name_parts[0]
        elif len(table_name_parts) == 3:
            details["table_name"] = table_name_parts[2]
            details["schema_name"] = table_name_parts[1]
            details["database_name"] = table_name_parts[0]
        else:
            raise ValueError(f"Invalid change history table name: {v}")
        # if the object name does not include '"' raise to upper case on return
        return cls(**{k: v if '"' in v else v.upper() for (k, v) in details.items()})


class DeployConfig(Config):
    subcommand: Literal["deploy"] = "deploy"
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_role: str | None = None
    snowflake_warehouse: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str | None = None
    # TODO: Turn change_history_table into three arguments. There's no need to parse it from a string
    change_history_table: Table | None = Field(default_factory=Table)
    create_change_history_table: bool = False
    autocommit: bool = False
    dry_run: bool = False
    query_tag: str | None = None
    oauth_config: dict | None = None
    version_number_validation_regex: str | None = None
    raise_exception_on_ignored_versioned_migration: bool = False

    def check_for_deploy_args(self) -> None:
        """Make sure we have the required connection info

        :return:
        """
        #
        req_args = {
            "snowflake_account": self.snowflake_account,
            "snowflake_user": self.snowflake_user,
            "snowflake_role": self.snowflake_role,
            "snowflake_warehouse": self.snowflake_warehouse,
        }
        missing_args = [key for key, value in req_args.items() if value is None]

        if len(missing_args) == 0:
            return

        missing_args = ", ".join({arg.replace("_", " ") for arg in missing_args})
        raise ValueError(
            f"Missing config values. The following config values are required: {missing_args}"
        )


class RenderConfig(DeployConfig):
    subcommand: Literal["render"] = "render"
    script_path: Path

    @field_validator("script_path")
    @classmethod
    def must_be_valid_file(cls, v: Path) -> Path | None:
        if not v.is_file():
            raise ValueError(f"invalid script_path: {str(v)}")
        return v


def config_factory(args: Namespace | dict) -> DeployConfig | RenderConfig:
    if isinstance(args, Namespace):
        subcommand = args.subcommand
        kwargs = args.__dict__
    else:
        subcommand = args.get("subcommand")
        kwargs = args

    if "change_history_table" in kwargs and kwargs["change_history_table"] is not None:
        kwargs["change_history_table"] = Table.from_str(kwargs["change_history_table"])

    if subcommand == "deploy":
        return DeployConfig(**kwargs)
    elif subcommand == "render":
        return RenderConfig(**kwargs)
    else:
        raise Exception(f"unhandled subcommand: {subcommand}")
