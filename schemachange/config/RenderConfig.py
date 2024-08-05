from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Literal

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.utils import validate_file_path


@dataclasses.dataclass(frozen=True, kw_only=True)
class RenderConfig(BaseConfig):
    subcommand: Literal["render"] = "render"
    script_path: Path

    @classmethod
    def factory(
        cls,
        script_path: Path | str,
        **kwargs,
    ):
        # Ignore Deploy arguments
        field_names = [field.name for field in dataclasses.fields(RenderConfig)]
        kwargs = {k: v for k, v in kwargs.items() if k in field_names}

        if "subcommand" in kwargs:
            kwargs.pop("subcommand")

        return super().factory(
            subcommand="render",
            script_path=validate_file_path(file_path=script_path),
            **kwargs,
        )
