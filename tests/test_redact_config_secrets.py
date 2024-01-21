import pytest

from schemachange.redact_config_secrets import get_redact_config_secrets_processor


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
def test_get_redact_config_secrets_processor(
    secrets: set[str], extra_kwargs: dict, expected: dict
):
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
def test_get_redact_config_secrets_processor_warnings(
    extra_kwargs: dict, expected_warning: str
):
    redact_config_secrets_processor = get_redact_config_secrets_processor(
        config_secrets={"secret"}
    )

    with pytest.warns(UserWarning) as e:
        # noinspection PyTypeChecker
        redact_config_secrets_processor(
            None, "info", {"event": "event text", "level": "info", **extra_kwargs}
        )

    assert expected_warning in str(e[0].message)
