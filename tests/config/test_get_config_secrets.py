from __future__ import annotations

import pytest

from schemachange.config.utils import get_config_secrets


def test_given_empty_config_should_not_error():
    get_config_secrets(config_vars={})


def test_given_none_should_not_error():
    get_config_secrets(None)


@pytest.mark.parametrize(
    "config_vars, secret",
    [
        ({"secret": "secret_val1"}, "secret_val1"),
        ({"SECret": "secret_val2"}, "secret_val2"),
        ({"secret_key": "secret_val3"}, "secret_val3"),
        ({"s3_bucket_secret": "secret_val4"}, "secret_val4"),
        ({"s3SecretKey": "secret_val5"}, "secret_val5"),
        ({"nested": {"s3_bucket_secret": "secret_val6"}}, "secret_val6"),
    ],
)
def test_given__vars_with_keys_should_extract_secret(config_vars, secret):
    results = get_config_secrets(config_vars)
    assert secret in results


def test_given_vars_with_secrets_key_then_all_children_should_be_treated_as_secrets():
    config_vars = {
        "secrets": {
            "database_name": "database_name_val",
            "schema_name": "schema_name_val",
            "nested_secrets": {"SEC_ONE": "SEC_ONE_VAL"},
        }
    }
    results = get_config_secrets(config_vars=config_vars)

    assert len(results) == 3
    assert "database_name_val" in results
    assert "schema_name_val" in results
    assert "SEC_ONE_VAL" in results


def test_given_vars_with_nested_secrets_key_then_all_children_should_be_treated_as_secrets():
    config_vars = {
        "nested": {
            "secrets": {
                "database_name": "database_name_val",
                "schema_name": "schema_name_val",
                "nested": {"SEC_ONE": "SEC_ONE_VAL"},
            }
        }
    }

    results = get_config_secrets(config_vars)

    assert len(results) == 3
    assert "database_name_val" in results
    assert "schema_name_val" in results
    assert "SEC_ONE_VAL" in results


def test_given_vars_with_same_secret_twice_then_only_extracted_once():
    config_vars = {
        "secrets": {
            "database_name": "SECRET_VALUE",
            "schema_name": "SECRET_VALUE",
            "nested_secrets": {"SEC_ONE": "SECRET_VALUE"},
        }
    }

    results = get_config_secrets(config_vars)

    assert len(results) == 1
    assert "SECRET_VALUE" in results
