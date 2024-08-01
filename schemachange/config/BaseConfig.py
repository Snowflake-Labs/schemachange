from __future__ import annotations

import dataclasses
import logging
from abc import ABC
from pathlib import Path
from typing import Literal, ClassVar, TypeVar

import structlog

from schemachange.config.utils import (
    validate_directory,
    validate_config_vars,
    get_config_secrets,
)

logger = structlog.getLogger(__name__)
T = TypeVar("T", bound="BaseConfig")


@dataclasses.dataclass(frozen=True, kw_only=True)
class BaseConfig(ABC):
    default_config_file_name: ClassVar[str] = "schemachange-config.yml"

    subcommand: Literal["deploy", "render"]
    config_version: int | None = None
    config_folder: Path = Path(".")
    config_file_path: Path | None = None
    root_folder: Path | None = Path(".")
    modules_folder: Path | None = None
    config_vars: dict = dataclasses.field(default_factory=dict)
    secrets: set[str] = dataclasses.field(default_factory=set)
    log_level: int = logging.INFO

    @classmethod
    def factory(
        cls,
        subcommand: Literal["deploy", "render"],
        config_folder: Path | str | None = Path("."),
        root_folder: Path | str | None = Path("."),
        modules_folder: Path | str | None = None,
        config_vars: str | dict | None = None,
        log_level: int = logging.INFO,
        **kwargs,
    ):
        if config_folder is None:
            config_folder = "."

        return cls(
            subcommand=subcommand,
            config_folder=validate_directory(path=config_folder),
            config_file_path=Path(config_folder) / cls.default_config_file_name,
            root_folder=validate_directory(path=root_folder),
            modules_folder=validate_directory(path=modules_folder),
            config_vars=validate_config_vars(config_vars=config_vars),
            secrets=get_config_secrets(config_vars),
            log_level=log_level,
            **kwargs,
        )

    def asdict_exclude_defaults(self) -> dict:
        retain = {}
        for field in dataclasses.fields(self):
            val = getattr(self, field.name)
            if (
                val is None
                and field.default == dataclasses.MISSING
                or val == field.default
            ):
                continue
            if (
                field.default_factory != dataclasses.MISSING
                and val == field.default_factory()
            ):
                continue
            if field.name in [
                "_create_change_history_table",
                "_autocommit",
                "_dry_run",
                "_raise_exception_on_ignored_versioned_script",
            ]:
                retain[field.name.lstrip("_")] = val
            else:
                retain[field.name] = val

        return retain

    def merge_exclude_defaults(self: T, other: T) -> T:
        self_kwargs = self.asdict_exclude_defaults()
        self_kwargs.pop("config_file_path")

        other_kwargs = other.asdict_exclude_defaults()
        other_kwargs.pop("config_file_path")
        if "change_history_table" in other_kwargs:
            other_kwargs["change_history_table"] = other.change_history_table

        if "secrets" in other_kwargs and len(other_kwargs["secrets"]) == 0:
            other_kwargs.pop("secrets")

        kwargs = {**self_kwargs, **other_kwargs}
        return self.__class__.factory(**kwargs)

    def log_details(self):
        logger.info("Using root folder", root_folder=str(self.root_folder))
        if self.modules_folder:
            logger.info(
                "Using Jinja modules folder", modules_folder=str(self.modules_folder)
            )

        logger.info("Using variables", vars=self.config_vars)
