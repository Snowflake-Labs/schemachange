from __future__ import annotations

import itertools
import re
from abc import ABC
from pathlib import Path
from typing import Literal, ClassVar, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar("T", bound="Script")


class Script(BaseModel, ABC):
    model_config = ConfigDict(frozen=True, extra="ignore")
    pattern: ClassVar[re.Pattern[str]]
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
    def from_path(cls, file_path: Path, verbose: bool = False, **kwargs) -> Script[T]:
        if verbose:
            print(f"Found {cls.__name__}: {str(file_path)}")

        # script name is the filename without any jinja extension
        script_name = cls.get_script_name(file_path=file_path)
        name_parts = cls.pattern.search(file_path.stem.strip())
        description = name_parts.group("description").replace("_", " ").capitalize()
        return cls(
            name=script_name, file_path=file_path, description=description, **kwargs
        )


class VersionedScript(Script):
    pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"^(V)(?P<version>.+?)?__(?P<description>.+?)\.", re.IGNORECASE
    )
    type: ClassVar[Literal["V"]] = "V"
    version: str

    @classmethod
    def from_path(cls: T, file_path: Path, verbose: bool = False, **kwargs) -> T:
        name_parts = cls.pattern.search(file_path.stem.strip())

        return super().from_path(
            file_path=file_path,
            verbose=verbose,
            version=name_parts.group("version"),
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


pattern_constructors: dict[
    re.Pattern[str], type[VersionedScript | RepeatableScript | AlwaysScript]
] = {
    VersionedScript.pattern: VersionedScript,
    RepeatableScript.pattern: RepeatableScript,
    AlwaysScript.pattern: AlwaysScript,
}


def script_factory(
    file_path: Path, verbose: bool = False
) -> VersionedScript | RepeatableScript | AlwaysScript | None:
    constructor: type[VersionedScript | RepeatableScript | AlwaysScript] | None = None
    for pattern in pattern_constructors.keys():
        name_parts = pattern.search(file_path.stem.strip())
        if name_parts is not None:
            constructor = pattern_constructors[pattern]
            break

    if constructor is None:
        if verbose:
            print(f"Ignoring non-change file {str(file_path)}")
        return

    return constructor.from_path(file_path=file_path, verbose=verbose)


def get_all_scripts_recursively(root_directory: Path, verbose: bool = False):
    all_files: dict[str, VersionedScript | RepeatableScript | AlwaysScript] = dict()
    all_versions = list()
    # Walk the entire directory structure recursively
    file_paths = itertools.chain(
        root_directory.rglob("*.sql"), root_directory.rglob("*.sql.jinja")
    )

    for file_path in file_paths:
        script = script_factory(file_path=file_path, verbose=verbose)

        # Throw an error if the script_name already exists
        if script.name in all_files:
            raise ValueError(
                f"The script name {script.name} exists more than once ("
                f"first_instance {str(all_files[script.name].file_path)}, "
                f"second instance {str(script.file_path)})"
            )

        all_files[script.name] = script

        # Throw an error if the same version exists more than once
        if script.type == "V":
            if script.version in all_versions:
                raise ValueError(
                    f"The script version {script.version} exists more than once "
                    f"(second instance {str(script.file_path)})"
                )
            all_versions.append(script["script_version"])

    return all_files
