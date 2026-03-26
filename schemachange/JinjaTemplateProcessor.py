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

    def _is_cli_script(self, script: str | Path) -> bool:
        """Check if the script is a CLI migration file (.cli.yml)."""
        script_lower = str(script).lower()
        return script_lower.endswith(".cli.yml") or script_lower.endswith(".cli.yml.jinja")

    def render(self, script: str, variables: dict[str, Any] | None) -> str:
        if not variables:
            variables = {}
        # jinja needs posix path
        posix_path = Path(script).as_posix()
        template = self.__environment.get_template(posix_path)
        raw_content = template.render(**variables)

        # Remove UTF-8 BOM if present (issue #250)
        # The BOM character (\ufeff) causes errors
        # Common in files saved with "UTF-8 with BOM" encoding (Windows/VS Code)
        if raw_content.startswith("\ufeff"):
            logger.debug("Removing UTF-8 BOM from script", script=script)
            raw_content = raw_content[1:]

        # For CLI scripts (.cli.yml), return the rendered YAML without SQL-specific processing
        if self._is_cli_script(script):
            content = raw_content.strip()
            if not content:
                raise ValueError(
                    f"CLI script '{script}' rendered to empty content after Jinja processing.\n"
                    f"Ensure the file contains valid YAML with a 'steps' key."
                )
            return content

        # SQL-specific processing below
        content = raw_content.strip()

        # Strip trailing semicolon for checksum stability (issue #417)
        # This ensures checksums remain consistent regardless of trailing semicolon
        content = content[:-1] if content.endswith(";") else content

        # Validate content is not empty after processing
        if not content or content.isspace():
            raise ValueError(
                f"Script '{script}' rendered to empty content. Check Jinja variables and conditional blocks."
            )

        # Check if content is only comments (would fail in Snowflake)
        content_without_comments = re.sub(r"--[^\n]*", "", content)
        content_without_comments = re.sub(r"/\*.*?\*/", "", content_without_comments, flags=re.DOTALL)
        content_without_comments = content_without_comments.replace(";", "").strip()

        if not content_without_comments:
            raise ValueError(
                f"Script '{script}' contains only comments or semicolons. Add SQL statements or remove the script."
            )

        # NOTE: Trailing comment handling is NOT done here to preserve checksum stability.
        # Use prepare_for_execution() before sending to Snowflake. (issue #414)
        return content

    def prepare_for_execution(self, content: str, script: str | Path) -> str:
        """Apply execution-time SQL transformations to rendered content.

        This handles Snowflake-specific quirks like trailing comments that would
        cause "Empty SQL Statement" errors. Call this AFTER checksum computation,
        BEFORE sending to Snowflake for execution.

        Args:
            content: The rendered script content (from render())
            script: The script path (for logging and CLI detection)

        Returns:
            Content ready for Snowflake execution

        Note:
            This separation ensures checksums are computed on user content,
            not on internal workarounds. See issue #414.
        """
        if self._is_cli_script(script):
            return content

        # Handle trailing comments after last semicolon (issue #258, #406)
        # When content after the last ; is only whitespace/comments, Snowflake's
        # execute_string() sees it as a new empty statement and errors.
        return self._handle_trailing_comments(content, str(script))

    def _find_last_real_semicolon(self, content: str) -> int:
        """Find the last semicolon that is NOT inside a comment.

        Returns the index of the last real semicolon, or -1 if none found.
        """
        # Track whether we're inside a comment
        i = 0
        last_real_semicolon = -1

        while i < len(content):
            # Check for single-line comment start
            if content[i : i + 2] == "--":
                # Skip to end of line
                newline_idx = content.find("\n", i)
                if newline_idx == -1:
                    break  # Rest of content is a comment
                i = newline_idx + 1
                continue

            # Check for multi-line comment start
            if content[i : i + 2] == "/*":
                # Skip to end of comment
                end_idx = content.find("*/", i + 2)
                if end_idx == -1:
                    break  # Rest of content is a comment
                i = end_idx + 2
                continue

            # Check for semicolon (not in a comment)
            if content[i] == ";":
                last_real_semicolon = i

            i += 1

        return last_real_semicolon

    def _handle_trailing_comments(self, content: str, script: str) -> str:
        """Append SELECT 1; if there are trailing comments on NEW LINES after the last semicolon.

        Snowflake's execute_string() splits on semicolons. If there's content after
        the last ; that is only whitespace/comments ON NEW LINES, Snowflake strips
        the comments and tries to execute an empty string, causing "Empty SQL Statement".

        Inline comments on the same line as ; are fine (e.g., "SELECT 1; -- comment")
        Only comments on separate lines after ; cause the error.

        This method detects that specific case and appends a no-op SELECT 1;
        """
        # Find the last semicolon that's NOT inside a comment
        last_semicolon_idx = self._find_last_real_semicolon(content)
        if last_semicolon_idx == -1:
            # No semicolon in content - Snowflake executes as single statement
            return content

        # Get content after the last real semicolon
        after_semicolon = content[last_semicolon_idx + 1 :]

        # Only problematic if there's a newline after the semicolon
        # Inline comments on the same line as ; are handled fine by Snowflake
        if "\n" not in after_semicolon:
            return content

        # Check if content after ; is only whitespace and/or comments
        after_stripped = after_semicolon
        # Remove single-line comments
        after_stripped = re.sub(r"--[^\n]*", "", after_stripped)
        # Remove multi-line comments
        after_stripped = re.sub(r"/\*.*?\*/", "", after_stripped, flags=re.DOTALL)
        # Remove whitespace
        after_stripped = after_stripped.strip()

        if not after_stripped and after_semicolon.strip():
            # There IS content after ; on new lines, but it's only comments
            # Append SELECT 1; to prevent empty statement error
            logger.debug(
                "Appending SELECT 1; to handle trailing comments after last semicolon",
                script=script,
            )
            content = content.rstrip() + "\nSELECT 1; -- schemachange: trailing comment fix"

        return content

    def relpath(self, file_path: Path):
        return file_path.relative_to(self.__project_root)
