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
        config_file_path: Path,
        root_folder: Path | str | None = Path("."),
        modules_folder: Path | str | None = None,
        config_vars: str | dict | None = None,
        log_level: int = logging.INFO,
        **kwargs,
    ):
        try:
            secrets = get_config_secrets(config_vars)
        except Exception as e:
            raise Exception(
                "config_vars did not parse correctly, please check its configuration"
            ) from e

        return cls(
            subcommand=subcommand,
            config_file_path=config_file_path,
            root_folder=validate_directory(path=root_folder),
            modules_folder=validate_directory(path=modules_folder),
            config_vars=validate_config_vars(config_vars=config_vars),
            secrets=secrets,
            log_level=log_level,
            **kwargs,
        )

    def log_details(self):
        logger.info("Using root folder", root_folder=str(self.root_folder))
        if self.modules_folder:
            logger.info(
                "Using Jinja modules folder", modules_folder=str(self.modules_folder)
            )

        logger.info("Using variables", vars=self.config_vars)
