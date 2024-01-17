from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Literal, ClassVar, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic_core.core_schema import ValidationInfo

T = TypeVar("T", bound="Config")


class Config(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    default_config_file_name: ClassVar[str] = "schemachange-config.yml"

    subcommand: Literal["deploy", "render"]
    config_folder: Path = Field(default=Path("."))
    config_file_path: Path | None = None
    root_folder: Path | None = Field(default=Path("."))
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

        return self.model_copy(update=other_kwargs)


class DeployConfig(Config):
    subcommand: Literal["deploy"] = "deploy"
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

    if subcommand == "deploy":
        return DeployConfig(**kwargs)
    elif subcommand == "render":
        return RenderConfig(**kwargs)
    else:
        raise Exception(f"unhandled subcommand: {subcommand}")
