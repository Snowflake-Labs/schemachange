from __future__ import annotations

import itertools
import re
from abc import ABC
from pathlib import Path
from typing import (
    Literal,
    ClassVar,
    TypeVar,
    Optional,
    Union,
    List,
    Dict,
    Type,
    Pattern,
)

import structlog
from pydantic import BaseModel, ConfigDict


logger = structlog.getLogger(__name__)
T = TypeVar("T", bound="Script")


class Script(BaseModel, ABC):
    model_config = ConfigDict(frozen=True, extra="ignore")
    pattern: ClassVar[Pattern[str]]
    type: ClassVar[Literal["V", "R", "A"]]
    name: str
    file_path: Path
    description: str

    @staticmethod
    def get_script_name(file_path: Path) -> str:
        """Script name is the filename without any jinja extension"""
        if file_path.suffixes[-1].upper() == ".JINJA":
            return file_path.stem
        return file_path.name

    @classmethod
    def from_path(cls, file_path: Path, **kwargs) -> Script[T]:
        logger.debug("script found", class_name=cls.__name__, file_path=str(file_path))

        # script name is the filename without any jinja extension
        script_name = cls.get_script_name(file_path=file_path)
        name_parts = cls.pattern.search(file_path.name.strip())
        description = name_parts.group("description").replace("_", " ").capitalize()
        return cls(
            name=script_name, file_path=file_path, description=description, **kwargs
        )


class VersionedScript(Script):
    pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"^(V)(?P<version>.+?)?__(?P<description>.+?)\.", re.IGNORECASE
    )
    type: ClassVar[Literal["V"]] = "V"
    version_number_regex: ClassVar[Optional[str]] = None
    version: str

    @classmethod
    def from_path(cls: T, file_path: Path, **kwargs) -> T:
        name_parts = cls.pattern.search(file_path.name.strip())

        if cls.version_number_regex:
            version = name_parts.group("version")
            if re.search(cls.version_number_regex, version, re.IGNORECASE) is None:
                raise ValueError(
                    f"change script version doesn't match the supplied regular expression: "
                    f"{cls.version_number_regex}\n{str(file_path)}"
                )

        return super().from_path(
            file_path=file_path, version=name_parts.group("version")
        )


class RepeatableScript(Script):
    pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"^(R)__(?P<description>.+?)\.", re.IGNORECASE
    )
    type: ClassVar[Literal["R"]] = "R"


class AlwaysScript(Script):
    pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"^(A)__(?P<description>.+?)\.", re.IGNORECASE
    )
    type: ClassVar[Literal["A"]] = "A"


constructors: List[Type[Union[VersionedScript, RepeatableScript, AlwaysScript]]] = [
    VersionedScript,
    RepeatableScript,
    AlwaysScript,
]


def script_factory(
    file_path: Path,
) -> Optional[Union[VersionedScript, RepeatableScript, AlwaysScript]]:
    constructor: Optional[
        Type[Union[VersionedScript, RepeatableScript, AlwaysScript]]
    ] = None
    for a_constructor in constructors:
        if a_constructor.pattern.search(file_path.name.strip()) is not None:
            constructor = a_constructor
            break

    if constructor is None:
        logger.debug("ignoring non-change file", file_path=str(file_path))
        return

    return constructor.from_path(file_path=file_path)


def get_all_scripts_recursively(
    root_directory: Path, version_number_regex: Optional[str] = None
):
    VersionedScript.version_number_regex = version_number_regex

    all_files: Dict[
        str, Union[VersionedScript, RepeatableScript, AlwaysScript]
    ] = dict()
    all_versions = list()
    # Walk the entire directory structure recursively
    file_paths = itertools.chain(
        root_directory.rglob("*.sql"), root_directory.rglob("*.sql.jinja")
    )

    for file_path in file_paths:
        script = script_factory(file_path=file_path)
        if script is None:
            continue

        # Throw an error if the script_name already exists
        if script.name.lower() in all_files:
            raise ValueError(
                f"The script name {script.name} exists more than once ("
                f"first_instance {str(all_files[script.name.lower()].file_path)}, "
                f"second instance {str(script.file_path)})"
            )

        all_files[script.name.lower()] = script

        # Throw an error if the same version exists more than once
        if script.type == "V":
            if script.version in all_versions:
                raise ValueError(
                    f"The script version {script.version} exists more than once "
                    f"(second instance {str(script.file_path)})"
                )
            all_versions.append(script.version)

    return all_files
