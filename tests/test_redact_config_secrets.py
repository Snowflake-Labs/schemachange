from __future__ import annotations


import pytest
import structlog

from schemachange.redact_config_secrets import (
    get_redact_config_secrets_processor,
    redact_config_secrets,
)


class TestRedactConfigSecrets:
    def test_skip_processor_config_with_empty_config_secrets(self):
        prev_cfg = structlog.get_config()
        redact_config_secrets(config_secrets=set())
        new_cfg = structlog.get_config()

        assert len(prev_cfg["processors"]) == len(new_cfg["processors"])

    def test_processor_config_with_populated_config_secrets(self):
        prev_cfg = structlog.get_config()
        redact_config_secrets(config_secrets={"secret"})
        new_cfg = structlog.get_config()

        assert len(prev_cfg["processors"]) == len(new_cfg["processors"])


class TestGetRedactConfigSecretsProcessor:
    @pytest.mark.parametrize(
        "secrets, extra_kwargs, expected",
        [
            ({}, {"keyword": "secret"}, {"keyword": "secret"}),
            ({}, {}, {}),
            ({"secret"}, {"keyword": "secret"}, {"keyword": "******"}),
            (
                {"secret"},
                {"keyword": {"keyword": "secret"}},
                {"keyword": {"keyword": "******"}},
            ),
            (
                {"secret"},
                {"keyword": {"keyword": {"keyword": "secret"}}},
                {"keyword": {"keyword": {"keyword": "******"}}},
            ),
            (
                {"secret"},
                {"keyword": {"keyword": {"keyword": "secret"}}},
                {"keyword": {"keyword": {"keyword": "******"}}},
            ),
            (
                {"12345"},
                {"keyword": {"keyword": {"keyword": 12345}}},
                {"keyword": {"keyword": {"keyword": "*****"}}},
            ),
        ],
    )
    def test_happy_path(self, secrets: set[str], extra_kwargs: dict, expected: dict):
        redact_config_secrets_processor = get_redact_config_secrets_processor(
            config_secrets=secrets
        )

        # noinspection PyTypeChecker
        result = redact_config_secrets_processor(
            None, "info", {"event": "event text", "level": "info", **extra_kwargs}
        )

        assert result == {"event": "event text", "level": "info", **expected}

    @pytest.mark.parametrize(
        "extra_kwargs, expected_warning",
        [
            (
                {
                    "keyword": {
                        "keyword": {
                            "keyword": {
                                "keyword": {
                                    "keyword": {
                                        "keyword": {"keyword": {"keyword": "secret"}}
                                    }
                                }
                            }
                        }
                    }
                },
                "Unable to redact deeply nested secrets in log",
            ),
            (
                {"keyword": object()},
                "Unable to redact object log arguments in log",
            ),
        ],
    )
    def test_warnings(self, extra_kwargs: dict, expected_warning: str):
        redact_config_secrets_processor = get_redact_config_secrets_processor(
            config_secrets={"secret"}
        )

        with pytest.warns(UserWarning) as e:
            # noinspection PyTypeChecker
            redact_config_secrets_processor(
                None, "info", {"event": "event text", "level": "info", **extra_kwargs}
            )

        assert expected_warning in str(e[0].message)
