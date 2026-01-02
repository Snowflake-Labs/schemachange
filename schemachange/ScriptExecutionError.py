"""Custom exception for script execution failures with rich context."""

from __future__ import annotations

from pathlib import Path


class ScriptExecutionError(Exception):
    """
    Exception raised when a script execution fails.

    Captures rich context about the failure including script details,
    SQL error codes, and the original exception for debugging.
    """

    def __init__(
        self,
        script_name: str,
        script_path: Path,
        script_type: str,
        error_message: str,
        sql_error_code: int | None = None,
        sql_state: str | None = None,
        query: str | None = None,
        original_exception: Exception | None = None,
    ):
        """
        Initialize ScriptExecutionError with rich context.

        Args:
            script_name: Name of the script that failed
            script_path: Path to the script file
            script_type: Type of script (V, R, or A)
            error_message: Human-readable error message
            sql_error_code: Snowflake SQL error code (if applicable)
            sql_state: Snowflake SQL state (if applicable)
            query: The SQL query that failed (optional, for debugging)
            original_exception: The original exception that was raised
        """
        self.script_name = script_name
        self.script_path = script_path
        self.script_type = script_type
        self.error_message = error_message
        self.sql_error_code = sql_error_code
        self.sql_state = sql_state
        self.query = query
        self.original_exception = original_exception

        # Create user-friendly message
        super().__init__(f"Failed to execute {script_type} script '{script_name}': {error_message}")

    def get_structured_error(self) -> dict:
        """
        Get error details as structured dict for logging.

        Returns:
            Dictionary with error details suitable for structured logging
        """
        return {
            "script_name": self.script_name,
            "script_path": self.script_path.as_posix(),
            "script_type": self.script_type,
            "error_message": self.error_message,
            "sql_error_code": self.sql_error_code,
            "sql_state": self.sql_state,
        }
