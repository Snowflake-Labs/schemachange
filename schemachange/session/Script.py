from __future__ import annotations

import dataclasses
import re
import time
from abc import ABC
from io import StringIO  # Required by split_statements - expects stream-like object
from pathlib import Path
from typing import (
    Literal,
    ClassVar,
    TypeVar,
    Pattern,
    TYPE_CHECKING,
)
from enum import Enum

import structlog
from snowflake.connector.util_text import split_statements

if TYPE_CHECKING:
    from .SnowflakeSession import SnowflakeSession

logger = structlog.getLogger(__name__)
T = TypeVar("T", bound="Script")


class ExecutionStatus(Enum):
    """Status of statement execution"""

    SUCCESS = "success"
    FAILED = "failed"


@dataclasses.dataclass
class ExecutionResult:
    """Result of executing a single statement"""

    statement: Statement
    status: ExecutionStatus
    error_message: str | None = None
    execution_time: float | None = None
    rows_affected: int | None = None
    query_id: str | None = None


@dataclasses.dataclass
class Statement:
    """Represents a single SQL statement with context"""

    sql_with_comments: str
    sql_without_comments: str
    line_number: int
    statement_index: int
    is_put_or_get: bool
    script_context: ScriptExecutionContext

    @property
    def sql(self) -> str:
        """Return the SQL with comments (primary accessor)"""
        return self.sql_with_comments

    @property
    def is_empty(self) -> bool:
        """Check if the statement is effectively empty based on the without-comments version"""
        return (
            not self.sql_without_comments
            or self.sql_without_comments.strip() == ""
            or self.sql_without_comments.strip() == ";"
        )

    def __str__(self) -> str:
        return f"Statement {self.statement_index} (line {self.line_number}): {self.sql[:50]}..."


@dataclasses.dataclass
class ScriptExecutionContext:
    """Context information about a script execution"""

    script_name: str
    script_type: str
    script_description: str
    script_version: str | None = None
    file_path: Path | None = None


class ScriptExecutionError(Exception):
    """Error raised when script execution fails"""

    def __init__(
        self,
        script_context: ScriptExecutionContext,
        statement: Statement,
        original_error: Exception,
    ):
        self.script_context = script_context
        self.statement = statement
        self.original_error = original_error
        super().__init__(
            f"Failed to execute {script_context.script_name} at statement {statement.statement_index} (line {statement.line_number}): {original_error}"
        )


class ScriptParsingError(Exception):
    """Error raised when script parsing fails"""

    def __init__(
        self, script_context: ScriptExecutionContext, original_error: Exception
    ):
        self.script_context = script_context
        self.original_error = original_error
        super().__init__(
            f"Failed to parse {script_context.script_name}: {original_error}"
        )


@dataclasses.dataclass
class ScriptExecutionReport:
    """Report of script execution results"""

    script_context: ScriptExecutionContext
    statements: list[Statement]
    results: list[ExecutionResult]
    total_execution_time: float
    success_count: int
    failure_count: int

    @property
    def is_successful(self) -> bool:
        return self.failure_count == 0

    def get_failed_statements(self) -> list[tuple[Statement, ExecutionResult]]:
        return [
            (result.statement, result)
            for result in self.results
            if result.status == ExecutionStatus.FAILED
        ]

    def get_successful_statements(self) -> list[tuple[Statement, ExecutionResult]]:
        return [
            (result.statement, result)
            for result in self.results
            if result.status == ExecutionStatus.SUCCESS
        ]


@dataclasses.dataclass(frozen=True)
class Script(ABC):
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
    def from_path(cls, file_path: Path, **kwargs) -> T:
        logger.debug("script found", class_name=cls.__name__, file_path=str(file_path))

        # script name is the filename without any jinja extension
        script_name = cls.get_script_name(file_path=file_path)
        name_parts = cls.pattern.search(file_path.name.strip())
        description = name_parts.group("description").replace("_", " ").capitalize()
        if len(name_parts.group("separator")) != 2:
            prefix = f"V{name_parts.group('version')}" if cls.type == "V" else cls.type

            raise ValueError(
                f'two underscores are required between "{ prefix }" and the description: '
                f"{file_path}\n{str(file_path)}"
            )
        # noinspection PyArgumentList
        return cls(
            name=script_name, file_path=file_path, description=description, **kwargs
        )

    def get_execution_context(self) -> ScriptExecutionContext:
        """Get the execution context for this script"""
        return ScriptExecutionContext(
            script_name=self.name,
            script_type=self.type,
            script_description=self.description,
            file_path=self.file_path,
        )

    def parse_statements(self, script_content: str) -> list[Statement]:
        """Parse the script content into executable statements with context"""
        try:
            context = self.get_execution_context()
            statements = []

            # Create StringIO from content - this feels clumsy but avoids reimplementing
            # the character-by-character parser in split_statements. The external method
            # expects a stream-like object for efficient parsing.
            stream = StringIO(script_content)

            # First, try to split statements with comments removed
            stream.seek(0)
            split_statements_without_comments = list(
                split_statements(stream, remove_comments=True)
            )

            # Reset stream position for second pass
            stream.seek(0)

            # Then split statements keeping comments
            split_statements_with_comments = list(
                split_statements(stream, remove_comments=False)
            )

            # Validate that both lists have the same length - they should always match
            if len(split_statements_without_comments) != len(
                split_statements_with_comments
            ):
                logger.warning(
                    f"Statement count mismatch in {self.name}: "
                    f"{len(split_statements_without_comments)} without comments vs "
                    f"{len(split_statements_with_comments)} with comments"
                )

            # Process each statement pair
            for i, (sql_with_comments, is_put_or_get_with_comments) in enumerate(
                split_statements_with_comments
            ):
                if i < len(split_statements_without_comments):
                    sql_without_comments, is_put_or_get_without_comments = (
                        split_statements_without_comments[i]
                    )
                else:
                    # This should never happen if the parsing is correct, but handle gracefully
                    sql_without_comments = sql_with_comments
                    is_put_or_get_without_comments = is_put_or_get_with_comments

                # Create Statement object with both SQL versions
                statement = Statement(
                    sql_with_comments=sql_with_comments,
                    sql_without_comments=sql_without_comments,
                    line_number=self._estimate_line_number(script_content, i),
                    statement_index=i + 1,
                    is_put_or_get=is_put_or_get_without_comments,  # Use the without-comments version for this flag
                    script_context=context,
                )
                statements.append(statement)

            return statements

        except Exception as e:
            context = self.get_execution_context()
            raise ScriptParsingError(context, e)

    def _estimate_line_number(self, content: str, statement_index: int) -> int:
        """Estimate the line number for a statement (simplified implementation)"""
        # This is a simplified implementation
        lines = content.split("\n")
        if statement_index < len(lines):
            return statement_index + 1
        return len(lines)

    def execute(
        self,
        session: SnowflakeSession,
        script_content: str,
        logger: structlog.BoundLogger,
    ) -> ScriptExecutionReport:
        """Execute this script and return a detailed execution report with warnings"""
        start_time = time.time()

        try:
            # Parse statements
            statements = self.parse_statements(script_content)
            logger.info(f"Parsed {len(statements)} statements from {self.name}")

            # Execute statements
            results = []
            execution_warnings = []

            for statement in statements:
                # Log warning for empty statements during execution
                if statement.is_empty:
                    logger.warning(
                        f"Empty SQL statement detected in {self.name} at position {statement.statement_index} "
                        f"(line {statement.line_number}): '{statement.sql}'"
                    )
                    execution_warnings.append(
                        f"Empty statement at position {statement.statement_index}"
                    )

                result = self.execute_single_script_statement(
                    statement, session, logger
                )
                results.append(result)

                # If a statement fails, we want to stop execution
                if result.status == ExecutionStatus.FAILED:
                    error_msg = f"Statement {statement.statement_index} failed, stopping execution"
                    logger.error(error_msg)
                    execution_warnings.append(error_msg)
                    break

            total_time = time.time() - start_time

            # Create execution report
            report = ScriptExecutionReport(
                script_context=self.get_execution_context(),
                statements=statements,
                results=results,
                total_execution_time=total_time,
                success_count=len(
                    [r for r in results if r.status == ExecutionStatus.SUCCESS]
                ),
                failure_count=len(
                    [r for r in results if r.status == ExecutionStatus.FAILED]
                ),
            )

            # Handle transaction management
            if report.failure_count > 0:
                # If any statement failed, rollback the transaction
                if not session.autocommit:
                    session.con.rollback()
                    logger.debug("Transaction rolled back due to statement failure")
            else:
                # If all statements succeeded, commit the transaction
                if not session.autocommit:
                    session.con.commit()
                    logger.debug("Transaction committed successfully")

            # Log execution summary
            if execution_warnings:
                logger.warning(
                    f"Execution completed with {len(execution_warnings)} warnings"
                )
            else:
                logger.info(f"Execution completed successfully in {total_time:.2f}s")

            return report

        except Exception as e:
            # Ensure rollback on any exception
            if not session.autocommit:
                session.con.rollback()
                logger.debug("Transaction rolled back due to exception")
            context = self.get_execution_context()
            raise ScriptExecutionError(context, None, e)

    def execute_single_script_statement(
        self,
        statement: Statement,
        session: SnowflakeSession,
        logger: structlog.BoundLogger,
    ) -> ExecutionResult:
        """Execute a single statement and return the result"""
        start_time = time.time()

        try:
            # Skip execution of empty statements
            if statement.is_empty:
                logger.debug(
                    f"Skipping empty statement {statement.statement_index} in {self.name}"
                )
                return ExecutionResult(
                    statement=statement,
                    status=ExecutionStatus.SUCCESS,
                    execution_time=0.0,
                    rows_affected=0,
                    query_id=None,
                )

            logger.debug(
                f"Executing statement {statement.statement_index}: {statement.sql[:100]}..."
            )

            # Execute the statement using the simplified session method
            # Use sql to preserve the original SQL as written
            # Don't auto-commit individual statements - let the script handle transaction management
            cursor = session.execute_snowflake_query(
                statement.sql, logger, auto_commit=False
            )

            execution_time = time.time() - start_time

            # Extract information from cursor
            query_id = getattr(cursor, "sfqid", None)
            rows_affected = getattr(cursor, "rowcount", None)

            return ExecutionResult(
                statement=statement,
                status=ExecutionStatus.SUCCESS,
                execution_time=execution_time,
                rows_affected=rows_affected,
                query_id=query_id,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Statement {statement.statement_index} failed: {e}")

            return ExecutionResult(
                statement=statement,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time=execution_time,
            )


@dataclasses.dataclass(frozen=True)
class VersionedScript(Script):
    pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"^(V)(?P<version>([^_]|_(?!_))+)?(?P<separator>_{1,2})(?P<description>.+?)\.",
        re.IGNORECASE,
    )
    type: ClassVar[Literal["V"]] = "V"
    version_number_regex: ClassVar[str | None] = None
    version: str

    @classmethod
    def from_path(cls: T, file_path: Path, **kwargs) -> T:
        name_parts = cls.pattern.search(file_path.name.strip())

        version = name_parts.group("version")
        if version is None:
            raise ValueError(
                f"Versioned migrations must be prefixed with a version: {str(file_path)}"
            )

        if cls.version_number_regex:
            if re.search(cls.version_number_regex, version, re.IGNORECASE) is None:
                raise ValueError(
                    f"change script version doesn't match the supplied regular expression: "
                    f"{cls.version_number_regex}\n{str(file_path)}"
                )

        return super().from_path(
            file_path=file_path, version=name_parts.group("version")
        )

    def get_execution_context(self) -> ScriptExecutionContext:
        """Get the execution context for this script with version information"""
        context = super().get_execution_context()
        context.script_version = self.version
        return context


@dataclasses.dataclass(frozen=True)
class RepeatableScript(Script):
    pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"^(R)(?P<separator>_{1,2})(?P<description>.+?)\.", re.IGNORECASE
    )
    type: ClassVar[Literal["R"]] = "R"


@dataclasses.dataclass(frozen=True)
class AlwaysScript(Script):
    pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"^(A)(?P<separator>_{1,2})(?P<description>.+?)\.", re.IGNORECASE
    )
    type: ClassVar[Literal["A"]] = "A"


def script_factory(
    file_path: Path,
) -> T | None:
    if VersionedScript.pattern.search(file_path.name.strip()) is not None:
        return VersionedScript.from_path(file_path=file_path)

    elif RepeatableScript.pattern.search(file_path.name.strip()) is not None:
        return RepeatableScript.from_path(file_path=file_path)

    elif AlwaysScript.pattern.search(file_path.name.strip()) is not None:
        return AlwaysScript.from_path(file_path=file_path)

    logger.debug("ignoring non-change file", file_path=str(file_path))


def get_all_scripts_recursively(
    root_directory: Path, version_number_regex: str | None = None
):
    VersionedScript.version_number_regex = version_number_regex

    all_files: dict[str, T] = dict()
    all_versions = list()
    # Walk the entire directory structure recursively
    sql_pattern = re.compile(r"\.sql(\.jinja)?$", flags=re.IGNORECASE)
    file_paths = root_directory.glob("**/*")
    for file_path in file_paths:
        if file_path.is_dir():
            continue
        if not sql_pattern.search(file_path.name.strip()):
            continue
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
