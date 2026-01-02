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


# "secrets, extra_kwargs, expected"
cases: list = [
    pytest.param(
        {},
        {},
        {},
        id="No secrets, No payload",
    ),
    pytest.param(
        {},
        {"key_1": None},
        {"key_1": "None"},
        id="No secrets, None payload unchanged",
    ),
    pytest.param(
        {},
        {"key_1": "secret"},
        {"key_1": "secret"},
        id="No secrets, string payload unchanged",
    ),
    pytest.param(
        {},
        {"key_1": b"secret"},
        {"key_1": str(b"secret")},
        id="No secrets, bytes payload unchanged",
    ),
    pytest.param(
        {},
        {"key_1": bytearray(5)},
        {"key_1": str(bytearray(5))},
        id="No secrets, bytearray payload unchanged",
    ),
    pytest.param(
        {},
        {"key_1": 3},
        {"key_1": str(3)},
        id="No secrets, int payload unchanged",
    ),
    pytest.param(
        {},
        {"key_1": 3.14},
        {"key_1": str(3.14)},
        id="No secrets, float payload unchanged",
    ),
    pytest.param(
        {},
        {"key_1": 3j},
        {"key_1": str(3j)},
        id="No secrets, complex payload unchanged",
    ),
    pytest.param(
        {},
        {"key_1": True},
        {"key_1": str(True)},
        id="No secrets, boolean payload unchanged",
    ),
    pytest.param(
        {},
        {"key_1": range(6)},
        {"key_1": str(range(6))},
        id="No secrets, range payload unchanged",
    ),
    pytest.param(
        {},
        {
            "key_1": [
                None,
                "secret",
                b"secret",
                bytearray(5),
                3,
                3.14,
                3j,
                True,
                range(6),
            ]
        },
        {
            "key_1": [
                str(None),
                "secret",
                str(b"secret"),
                str(bytearray(5)),
                str(3),
                str(3.14),
                str(3j),
                str(True),
                str(range(6)),
            ]
        },
        id="No secrets, list payload unchanged",
    ),
    pytest.param(
        {},
        {
            "key_1": (
                None,
                "secret",
                b"secret",
                bytearray(5),
                3,
                3.14,
                3j,
                True,
                range(6),
            )
        },
        {
            "key_1": (
                str(None),
                "secret",
                str(b"secret"),
                str(bytearray(5)),
                str(3),
                str(3.14),
                str(3j),
                str(True),
                str(range(6)),
            )
        },
        id="No secrets, tuple payload unchanged",
    ),
    pytest.param(
        {},
        {
            "key_1": {
                None,
                "secret",
                b"secret",
                3,
                3.14,
                3j,
                True,
                range(6),
            }
        },
        {
            "key_1": {
                str(None),
                "secret",
                str(b"secret"),
                str(3),
                str(3.14),
                str(3j),
                str(True),
                str(range(6)),
            }
        },
        id="No secrets, set payload unchanged",
    ),
    pytest.param(
        {},
        {
            "key_1": {
                "key_2a": None,
                "key_2b": "secret",
                "key_2c": b"secret",
                "key_2d": bytearray(5),
                "key_2e": 3,
                "key_2f": 3.14,
                "key_2g": 3j,
                "key_2h": True,
                "key_2i": range(6),
                "key_2j": [
                    None,
                    "secret",
                    b"secret",
                    bytearray(5),
                    3,
                    3.14,
                    3j,
                    True,
                    range(6),
                ],
                "key_2k": (
                    None,
                    "secret",
                    b"secret",
                    bytearray(5),
                    3,
                    3.14,
                    3j,
                    True,
                    range(6),
                ),
                "key_2l": {
                    None,
                    "secret",
                    b"secret",
                    3,
                    3.14,
                    3j,
                    True,
                    range(6),
                },
            }
        },
        {
            "key_1": {
                "key_2a": str(None),
                "key_2b": "secret",
                "key_2c": str(b"secret"),
                "key_2d": str(bytearray(5)),
                "key_2e": str(3),
                "key_2f": str(3.14),
                "key_2g": str(3j),
                "key_2h": str(True),
                "key_2i": str(range(6)),
                "key_2j": [
                    str(None),
                    "secret",
                    str(b"secret"),
                    str(bytearray(5)),
                    str(3),
                    str(3.14),
                    str(3j),
                    str(True),
                    str(range(6)),
                ],
                "key_2k": (
                    str(None),
                    "secret",
                    str(b"secret"),
                    str(bytearray(5)),
                    str(3),
                    str(3.14),
                    str(3j),
                    str(True),
                    str(range(6)),
                ),
                "key_2l": {
                    str(None),
                    "secret",
                    str(b"secret"),
                    str(3),
                    str(3.14),
                    str(3j),
                    str(True),
                    str(range(6)),
                },
            }
        },
        id="No secrets, dict payload unchanged",
    ),
    pytest.param(
        {},
        {
            "key_1": {
                "key_2": {
                    "key_3a": None,
                    "key_3b": "secret",
                    "key_3c": b"secret",
                    "key_3d": bytearray(5),
                    "key_3e": 3,
                    "key_3f": 3.14,
                    "key_3g": 3j,
                    "key_3h": True,
                    "key_3i": range(6),
                    "key_3j": [
                        None,
                        "secret",
                        b"secret",
                        bytearray(5),
                        3,
                        3.14,
                        3j,
                        True,
                        range(6),
                    ],
                    "key_3k": (
                        None,
                        "secret",
                        b"secret",
                        bytearray(5),
                        3,
                        3.14,
                        3j,
                        True,
                        range(6),
                    ),
                    "key_3l": {
                        None,
                        "secret",
                        b"secret",
                        3,
                        3.14,
                        3j,
                        True,
                        range(6),
                    },
                }
            }
        },
        {
            "key_1": {
                "key_2": {
                    "key_3a": str(None),
                    "key_3b": "secret",
                    "key_3c": str(b"secret"),
                    "key_3d": str(bytearray(5)),
                    "key_3e": str(3),
                    "key_3f": str(3.14),
                    "key_3g": str(3j),
                    "key_3h": str(True),
                    "key_3i": str(range(6)),
                    "key_3j": [
                        str(None),
                        "secret",
                        str(b"secret"),
                        str(bytearray(5)),
                        str(3),
                        str(3.14),
                        str(3j),
                        str(True),
                        str(range(6)),
                    ],
                    "key_3k": (
                        str(None),
                        "secret",
                        str(b"secret"),
                        str(bytearray(5)),
                        str(3),
                        str(3.14),
                        str(3j),
                        str(True),
                        str(range(6)),
                    ),
                    "key_3l": {
                        str(None),
                        "secret",
                        str(b"secret"),
                        str(3),
                        str(3.14),
                        str(3j),
                        str(True),
                        str(range(6)),
                    },
                }
            }
        },
        id="No secrets, nested x 1 dict payload unchanged",
    ),
    pytest.param(
        {"secret", "3.14"},
        {},
        {},
        id="Secrets, No payload",
    ),
    pytest.param(
        {"secret", "3.14"},
        {"key_1": None},
        {"key_1": "None"},
        id="Secrets, None payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {"key_1": "secret"},
        {"key_1": "******"},
        id="Secrets, string payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {"key_1": b"secret"},
        {"key_1": str(b"******")},
        id="Secrets, bytes payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {"key_1": bytearray(5)},
        {"key_1": str(bytearray(5))},
        id="Secrets, bytearray payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {"key_1": 3},
        {"key_1": str(3)},
        id="Secrets, int payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {"key_1": 3.14},
        {"key_1": "****"},
        id="Secrets, float payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {"key_1": 3j},
        {"key_1": str(3j)},
        id="Secrets, complex payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {"key_1": True},
        {"key_1": str(True)},
        id="Secrets, boolean payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {"key_1": range(6)},
        {"key_1": str(range(6))},
        id="Secrets, range payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {
            "key_1": [
                None,
                "secret",
                b"secret",
                bytearray(5),
                3,
                3.14,
                3j,
                True,
                range(6),
            ]
        },
        {
            "key_1": [
                str(None),
                "******",
                str(b"******"),
                str(bytearray(5)),
                str(3),
                "****",
                str(3j),
                str(True),
                str(range(6)),
            ]
        },
        id="Secrets, list payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {
            "key_1": (
                None,
                "secret",
                b"secret",
                bytearray(5),
                3,
                3.14,
                3j,
                True,
                range(6),
            )
        },
        {
            "key_1": (
                str(None),
                "******",
                str(b"******"),
                str(bytearray(5)),
                str(3),
                "****",
                str(3j),
                str(True),
                str(range(6)),
            )
        },
        id="Secrets, tuple payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {
            "key_1": {
                None,
                "secret",
                b"secret",
                3,
                3.14,
                3j,
                True,
                range(6),
            }
        },
        {
            "key_1": {
                str(None),
                "******",
                str(b"******"),
                str(3),
                "****",
                str(3j),
                str(True),
                str(range(6)),
            }
        },
        id="Secrets, set payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {
            "key_1": {
                "key_2a": None,
                "key_2b": "secret",
                "key_2c": b"secret",
                "key_2d": bytearray(5),
                "key_2e": 3,
                "key_2f": 3.14,
                "key_2g": 3j,
                "key_2h": True,
                "key_2i": range(6),
                "key_2j": [
                    None,
                    "secret",
                    b"secret",
                    bytearray(5),
                    3,
                    3.14,
                    3j,
                    True,
                    range(6),
                ],
                "key_2k": (
                    None,
                    "secret",
                    b"secret",
                    bytearray(5),
                    3,
                    3.14,
                    3j,
                    True,
                    range(6),
                ),
                "key_2l": {
                    None,
                    "secret",
                    b"secret",
                    3,
                    3.14,
                    3j,
                    True,
                    range(6),
                },
            }
        },
        {
            "key_1": {
                "key_2a": str(None),
                "key_2b": "******",
                "key_2c": str(b"******"),
                "key_2d": str(bytearray(5)),
                "key_2e": str(3),
                "key_2f": "****",
                "key_2g": str(3j),
                "key_2h": str(True),
                "key_2i": str(range(6)),
                "key_2j": [
                    str(None),
                    "******",
                    str(b"******"),
                    str(bytearray(5)),
                    str(3),
                    "****",
                    str(3j),
                    str(True),
                    str(range(6)),
                ],
                "key_2k": (
                    str(None),
                    "******",
                    str(b"******"),
                    str(bytearray(5)),
                    str(3),
                    "****",
                    str(3j),
                    str(True),
                    str(range(6)),
                ),
                "key_2l": {
                    str(None),
                    "******",
                    str(b"******"),
                    str(3),
                    "****",
                    str(3j),
                    str(True),
                    str(range(6)),
                },
            }
        },
        id="Secrets, dict payload masked",
    ),
    pytest.param(
        {"secret", "3.14"},
        {
            "key_1": {
                "key_2": {
                    "key_3a": None,
                    "key_3b": "secret",
                    "key_3c": b"secret",
                    "key_3d": bytearray(5),
                    "key_3e": 3,
                    "key_3f": 3.14,
                    "key_3g": 3j,
                    "key_3h": True,
                    "key_3i": range(6),
                    "key_3j": [
                        None,
                        "secret",
                        b"secret",
                        bytearray(5),
                        3,
                        3.14,
                        3j,
                        True,
                        range(6),
                    ],
                    "key_3k": (
                        None,
                        "secret",
                        b"secret",
                        bytearray(5),
                        3,
                        3.14,
                        3j,
                        True,
                        range(6),
                    ),
                    "key_3l": {
                        None,
                        "secret",
                        b"secret",
                        3,
                        3.14,
                        3j,
                        True,
                        range(6),
                    },
                }
            }
        },
        {
            "key_1": {
                "key_2": {
                    "key_3a": str(None),
                    "key_3b": "******",
                    "key_3c": str(b"******"),
                    "key_3d": str(bytearray(5)),
                    "key_3e": str(3),
                    "key_3f": "****",
                    "key_3g": str(3j),
                    "key_3h": str(True),
                    "key_3i": str(range(6)),
                    "key_3j": [
                        str(None),
                        "******",
                        str(b"******"),
                        str(bytearray(5)),
                        str(3),
                        "****",
                        str(3j),
                        str(True),
                        str(range(6)),
                    ],
                    "key_3k": (
                        str(None),
                        "******",
                        str(b"******"),
                        str(bytearray(5)),
                        str(3),
                        "****",
                        str(3j),
                        str(True),
                        str(range(6)),
                    ),
                    "key_3l": {
                        str(None),
                        "******",
                        str(b"******"),
                        str(3),
                        "****",
                        str(3j),
                        str(True),
                        str(range(6)),
                    },
                }
            }
        },
        id="Secrets, nested x 1 dict payload masked",
    ),
    pytest.param(
        {"secret", "12345"},
        {"key_1": {"key_2": {"key_3a": "secret", "key_3b": 12345}}},
        {"key_1": {"key_2": {"key_3a": "******", "key_3b": "*****"}}},
        id="Secrets, nested x 2 dict payload masked",
    ),
    pytest.param(
        {"multiline_secret\nwith_newlines"},
        {"key_1": "This contains multiline_secret\nwith_newlines in it"},
        {"key_1": "This contains ****************\n************* in it"},
        id="multiline secret redacted with newlines preserved (PR #238 by @rwberendsen)",
    ),
    pytest.param(
        {"line1\nline2\nline3"},
        {"azure_cert": "line1\nline2\nline3"},
        {"azure_cert": "*****\n*****\n*****"},
        id="multiline certificate redacted preserving structure (issue #237)",
    ),
]


class NoStr:
    def __str__(self):
        raise NotImplementedError()


class TestGetRedactConfigSecretsProcessor:
    @pytest.mark.parametrize("secrets, extra_kwargs, expected", cases)
    def test_happy_path(self, secrets: set[str], extra_kwargs: dict, expected: dict):
        redact_config_secrets_processor = get_redact_config_secrets_processor(config_secrets=secrets)

        # noinspection PyTypeChecker
        result = redact_config_secrets_processor(None, "info", {"event": "event text", "level": "info", **extra_kwargs})

        assert result == {"event": "event text", "level": "info", **expected}

    @pytest.mark.parametrize(
        "extra_kwargs, expected_warning",
        [
            (
                {"key_1": {"key_1": {"key_1": {"key_1": {"key_1": {"key_1": {"key_1": {"key_1": "secret"}}}}}}}},
                "Unable to redact deeply nested secrets in log",
            ),
            (
                {"key_1": NoStr()},
                "Unable to redact NoStr log arguments in log",
            ),
        ],
    )
    def test_warnings(self, extra_kwargs: dict, expected_warning: str):
        redact_config_secrets_processor = get_redact_config_secrets_processor(config_secrets={"secret"})

        with pytest.warns(UserWarning) as e:
            # noinspection PyTypeChecker
            redact_config_secrets_processor(None, "info", {"event": "event text", "level": "info", **extra_kwargs})

        assert expected_warning in str(e[0].message)
