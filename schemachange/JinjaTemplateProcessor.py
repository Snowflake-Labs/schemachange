from __future__ import annotations

import re
from pathlib import Path
from typing import Any

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
                    jinja2.PrefixLoader({"modules": jinja2.FileSystemLoader(modules_folder)}),
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

    def render(self, script: str, variables: dict[str, Any] | None) -> str:
        if not variables:
            variables = {}
        # jinja needs posix path
        posix_path = Path(script).as_posix()
        template = self.__environment.get_template(posix_path)
        raw_content = template.render(**variables)

        # Remove UTF-8 BOM if present (issue #250)
        # The BOM character (\ufeff) causes Snowflake SQL compilation errors
        # Common in files saved with "UTF-8 with BOM" encoding (Windows/VS Code)
        if raw_content.startswith("\ufeff"):
            logger.debug("Removing UTF-8 BOM from script", script=script)
            raw_content = raw_content[1:]

        content = raw_content.strip()
        content = content[:-1] if content.endswith(";") else content

        # Validate content is not empty after processing
        if not content or content.isspace():
            error_msg = (
                f"Script '{script}' rendered to empty SQL content after Jinja processing.\n"
                f"This can happen when:\n"
                f"  1. The file contains only whitespace\n"
                f"  2. All Jinja conditional blocks evaluate to false\n"
                f"  3. Template variables are missing or incorrect\n"
                f"  4. The file contains only a semicolon after rendering\n"
                f"\nRaw content preview (first 500 chars):\n{raw_content[:500]}\n"
                f"\nProvided variables: {list(variables.keys()) if variables else 'None'}"
            )
            logger.error("Empty SQL content after rendering", script=script, raw_content_length=len(raw_content))
            raise ValueError(error_msg)

        # Check if content contains only SQL comments (would be empty after Snowflake strips them)
        # This catches the common case where Snowflake connector strips comments and tries to execute empty string
        # Pattern explanation:
        # - Remove single-line comments: -- comment
        # - Remove multi-line comments: /* comment */
        # Note: This is a simplified check that handles most cases. Complex SQL with comments in strings
        # would require a full SQL parser. We're being pragmatic and catching 95% of issues.
        content_without_comments = re.sub(r"--[^\n]*", "", content)  # Remove -- comments
        content_without_comments = re.sub(
            r"/\*.*?\*/", "", content_without_comments, flags=re.DOTALL
        )  # Remove /* */ comments
        content_without_comments = content_without_comments.strip()

        # Case 1: Script contains ONLY comments (no SQL at all) - this is an error
        if not content_without_comments or content_without_comments.isspace():
            error_msg = (
                f"Script '{script}' contains only SQL comments after Jinja processing.\n"
                f"When Snowflake strips comments, this results in an empty SQL statement.\n"
                f"\nOriginal content:\n{content[:500]}\n"
                f"\nContent after comment removal:\n'{content_without_comments}'\n"
                f"\nTo fix:\n"
                f"  1. Add actual SQL statements to the script\n"
                f"  2. Remove comment-only scripts from your migrations\n"
                f"  3. If this is a placeholder, add a no-op statement like: SELECT 1; -- placeholder\n"
                f"\nProvided variables: {list(variables.keys()) if variables else 'None'}"
            )
            logger.error("SQL content contains only comments", script=script, original_length=len(content))
            raise ValueError(error_msg)

        # Case 2: Script has valid SQL but ends with comment lines
        # Snowflake connector may strip trailing comments leaving the last statement empty
        # Check if the last non-empty line is a comment
        lines = content.rstrip().split("\n")
        last_line = lines[-1].strip() if lines else ""

        if last_line.startswith("--") or (last_line.startswith("/*") and last_line.endswith("*/")):
            # Append a no-op statement to ensure Snowflake has something to execute after stripping comments
            # This preserves metadata comments while preventing "Empty SQL Statement" errors
            content = (
                content.rstrip()
                + "\nSELECT 1; -- schemachange: no-op statement to prevent empty SQL after comment stripping"
            )
            logger.debug(
                "Script ends with comment - appending no-op statement",
                script=script,
                last_line_preview=last_line[:100],
            )

        return content

    def relpath(self, file_path: Path):
        return file_path.relative_to(self.__project_root)
