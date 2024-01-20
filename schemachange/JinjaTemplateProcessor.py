from __future__ import annotations

from pathlib import Path

import jinja2
import jinja2.ext
import structlog
from jinja2.loaders import BaseLoader

from schemachange.JinjaEnvVar import JinjaEnvVar


logger = structlog.getLogger(__name__)


class JinjaTemplateProcessor:
    _env_args = {
        "undefined": jinja2.StrictUndefined,
        "autoescape": False,
        "extensions": [JinjaEnvVar],
    }

    def __init__(self, project_root: Path, modules_folder: Path = None):
        loader: BaseLoader
        if modules_folder:
            loader = jinja2.ChoiceLoader(
                [
                    jinja2.FileSystemLoader(project_root),
                    jinja2.PrefixLoader(
                        {"modules": jinja2.FileSystemLoader(modules_folder)}
                    ),
                ]
            )
        else:
            loader = jinja2.FileSystemLoader(project_root)
        self.__environment = jinja2.Environment(loader=loader, **self._env_args)
        self.__project_root = project_root

    def list(self):
        return self.__environment.list_templates()

    def override_loader(self, loader: jinja2.BaseLoader):
        # to make unit testing easier
        self.__environment = jinja2.Environment(loader=loader, **self._env_args)

    def render(self, script: str, vars: dict[str, object] | None) -> str:
        if not vars:
            vars = {}
        # jinja needs posix path
        posix_path = Path(script).as_posix()
        template = self.__environment.get_template(posix_path)
        content = template.render(**vars).strip()
        content = content[:-1] if content.endswith(";") else content
        return content

    def relpath(self, file_path: Path):
        return file_path.relative_to(self.__project_root)
