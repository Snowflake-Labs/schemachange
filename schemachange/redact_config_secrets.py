from __future__ import annotations

import warnings
from typing import Callable, Set

import structlog
from structlog import PrintLogger


def get_redact_config_secrets_processor(
    config_secrets: Set[str],
) -> Callable[[PrintLogger, str, dict], dict]:
    def redact_config_secrets_processor(
        _: PrintLogger, __: str, event_dict: dict
    ) -> dict:
        def redact_dict(level: int, sub_event_dict: dict) -> dict:
            if level > 6:
                warnings.warn(
                    "Unable to redact deeply nested secrets in log: %(event)s"
                    % {"event": event_dict["event"]}
                )
                return sub_event_dict
            for sub_k, sub_v in sub_event_dict.items():
                if isinstance(sub_v, dict):
                    sub_event_dict[sub_k] = redact_dict(
                        level=level + 1, sub_event_dict=sub_v
                    )
                elif isinstance(sub_v, str):
                    for secret in config_secrets:
                        if secret in sub_v:
                            sub_event_dict[sub_k] = sub_event_dict[sub_k].replace(
                                secret, "*" * len(secret)
                            )
                elif isinstance(sub_v, int):
                    for secret in config_secrets:
                        if secret in str(sub_v):
                            sub_event_dict[sub_k] = str(sub_event_dict[sub_k]).replace(
                                secret, "*" * len(secret)
                            )
                else:
                    warnings.warn(
                        "Unable to redact %(type)s log arguments in log: %(event)s"
                        % {"type": type(sub_v).__name__, "event": event_dict["event"]}
                    )
                    return sub_event_dict
            return sub_event_dict

        return redact_dict(level=0, sub_event_dict=event_dict)

    return redact_config_secrets_processor


def redact_config_secrets(config_secrets: Set[str]) -> None:
    if not config_secrets:
        return

    cfg = structlog.get_config()
    redact_config_secrets_processor = get_redact_config_secrets_processor(
        config_secrets=config_secrets
    )

    new_processors = cfg["processors"]
    new_processors.insert(len(cfg["processors"]) - 1, redact_config_secrets_processor)

    structlog.configure(processors=new_processors)
