from enum import Enum


class ChecksumChangedAction(Enum):
    """Action to take when a versioned script's checksum has changed since it was applied.

    IGNORE (default): Log info message and skip the script (current behavior)
    ERROR: Raise an exception and fail the deployment
    EXECUTE: Re-execute the modified script (useful for development)
    """

    IGNORE = "IGNORE"
    ERROR = "ERROR"
    EXECUTE = "EXECUTE"
