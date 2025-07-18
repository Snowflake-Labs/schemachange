from __future__ import annotations

import copy
import warnings
from typing import Callable, Any

import structlog
from structlog import PrintLogger


def get_redact_config_secrets_processor(
    config_secrets: set[str],
) -> Callable[[PrintLogger, str, dict], dict]:
    def redact_config_secrets_processor(
        _: PrintLogger, __: str, event_dict: dict
    ) -> dict:
        def redact_value(level: int, value: Any):
            if level > 6:
                warnings.warn(
                    "Unable to redact deeply nested secrets in log: %(event)s"
                    % {"event": event_dict["event"]}
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
                return tuple(
                    redact_value(level=level + 1, value=sub_v) for sub_v in value
                )
            elif not isinstance(value, str):
                try:
                    value = str(value)
                except Exception:
                    warnings.warn(
                        "Unable to redact %(type)s log arguments in log: %(event)s"
                        % {"type": type(value).__name__, "event": event_dict["event"]}
                    )
                    return value
            for secret in config_secrets:
                value = value.replace(secret, "*" * len(secret))
            return value

        return redact_value(level=0, value=copy.deepcopy(event_dict))

    return redact_config_secrets_processor


def redact_config_secrets(config_secrets: set[str]) -> None:
    if not config_secrets:
        return

    cfg = structlog.get_config()
    redact_config_secrets_processor = get_redact_config_secrets_processor(
        config_secrets=config_secrets
    )

    new_processors = cfg["processors"]
    new_processors.insert(len(cfg["processors"]) - 1, redact_config_secrets_processor)

    structlog.configure(processors=new_processors)
