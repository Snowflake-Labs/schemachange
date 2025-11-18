from __future__ import annotations

import copy
import warnings
from collections.abc import Callable
from typing import Any

import structlog
from structlog import PrintLogger


def get_redact_config_secrets_processor(
    config_secrets: set[str],
) -> Callable[[PrintLogger, str, dict], dict]:
    def redact_config_secrets_processor(_: PrintLogger, __: str, event_dict: dict) -> dict:
        def redact_value(level: int, value: Any):
            if level > 6:
                warnings.warn(
                    f"Unable to redact deeply nested secrets in log: {event_dict['event']}",
                    stacklevel=2,
                )
                return value
            if isinstance(value, dict):
                for sub_k, sub_v in value.items():
                    value[sub_k] = redact_value(level=level + 1, value=sub_v)
                return value
            elif isinstance(value, list):
                for i, sub_v in enumerate(value):
                    value[i] = redact_value(level=level + 1, value=sub_v)
                return value
            elif isinstance(value, set):
                return {redact_value(level=level + 1, value=sub_v) for sub_v in value}
            elif isinstance(value, tuple):
                return tuple(redact_value(level=level + 1, value=sub_v) for sub_v in value)
            elif not isinstance(value, str):
                try:
                    value = str(value)
                except Exception:
                    warnings.warn(
                        f"Unable to redact {type(value).__name__} log arguments in log: {event_dict['event']}",
                        stacklevel=2,
                    )
                    return value

            # Redact secrets while preserving newlines for readability
            # Credit: Enhancement from PR #238 by @rwberendsen
            # For multi-line secrets, showing "***\n***" is more readable than "******"
            for secret in config_secrets:
                if secret in value:
                    # Preserve newline structure in redaction for better readability
                    if "\n" in secret:
                        # Replace each line of the secret with asterisks, preserving newlines
                        secret_lines = secret.split("\n")
                        redacted_lines = ["*" * len(line) if line else "" for line in secret_lines]
                        redacted_secret = "\n".join(redacted_lines)
                        value = value.replace(secret, redacted_secret)
                    else:
                        # Single-line secret: replace with asterisks
                        value = value.replace(secret, "*" * len(secret))
            return value

        return redact_value(level=0, value=copy.deepcopy(event_dict))

    return redact_config_secrets_processor


def redact_config_secrets(config_secrets: set[str]) -> None:
    if not config_secrets:
        return

    cfg = structlog.get_config()
    redact_config_secrets_processor = get_redact_config_secrets_processor(config_secrets=config_secrets)

    new_processors = cfg["processors"]
    new_processors.insert(len(cfg["processors"]) - 1, redact_config_secrets_processor)

    structlog.configure(processors=new_processors)
