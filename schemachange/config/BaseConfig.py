from __future__ import annotations

import dataclasses
import logging
from abc import ABC
from pathlib import Path
from typing import Literal, TypeVar

import structlog

from schemachange.config.utils import (
    get_config_secrets,
    validate_config_vars,
    validate_directory,
)

logger = structlog.getLogger(__name__)
T = TypeVar("T", bound="BaseConfig")


@dataclasses.dataclass(frozen=True)
class BaseConfig(ABC):
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
        auth_secrets: dict[str, str] | None = None,
        **kwargs,
    ):
        try:
            secrets = get_config_secrets(config_vars, auth_secrets)
        except Exception as e:
            raise Exception("config_vars did not parse correctly, please check its configuration") from e

        # Get the field names from the dataclass to validate against
        field_names = {field.name for field in dataclasses.fields(cls)}

        # Check for unknown keys and warn about them
        # Note: auth_secrets is not a field, so we need to exclude it
        kwargs_to_check = {k: v for k, v in kwargs.items() if k != "auth_secrets"}
        unknown_keys = set(kwargs_to_check.keys()) - field_names
        if unknown_keys:
            unknown_keys_str = ", ".join(sorted(unknown_keys))
            logger.warning(f"Unknown configuration keys found and will be ignored: {unknown_keys_str}")
            # Filter out unknown keys to prevent TypeError
            kwargs = {k: v for k, v in kwargs.items() if k in field_names}

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
            logger.info("Using Jinja modules folder", modules_folder=str(self.modules_folder))

        logger.info("Using variables", vars=self.config_vars)
