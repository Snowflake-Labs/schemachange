import pytest
from schemachange.cli import extract_config_secrets

def test_extract_config_secrets_given_empty_config_should_not_error():
    config = {}
    results = extract_config_secrets(config)


def test_extract_config_secrets_given_None_should_not_error():
    results = extract_config_secrets(None)


@pytest.mark.parametrize("config, secret", [
    ({"vars": {"secret" : "secret_val1"}}, "secret_val1"),
    ({"vars": {"SECret" : "secret_val2"}}, "secret_val2"),
    ({"vars": {"secret_key" : "secret_val3"}}, "secret_val3"),
    ({"vars": {"s3_bucket_secret" : "secret_val4"}}, "secret_val4"),
    ({"vars": {"s3SecretKey" : "secret_val5"}}, "secret_val5"),
    ({"vars": { "nested" : {"s3_bucket_secret" : "secret_val6"}}}, "secret_val6"),
])
def test_extract_config_secrets_given__vars_with_keys_should_extract_secret(config, secret):
    results = extract_config_secrets(config)
    assert secret in results


def test_extract_config_secrets_given__vars_with_secrets_key_then_all_children_should_be_treated_as_secrets():
    config = {"vars": {"secrets" : {"database_name": "database_name_val", "schema_name": "schema_name_val", "nested_secrets": {"SEC_ONE": "SEC_ONE_VAL"  } } }}

    results = extract_config_secrets(config)

    assert len(results) == 3
    assert "database_name_val" in results
    assert "schema_name_val" in results
    assert "SEC_ONE_VAL" in results


def test_extract_config_secrets_given__vars_with_nested_secrets_key_then_all_children_should_be_treated_as_secrets():
    config = {"vars": {"nested": {"secrets" : {"database_name": "database_name_val", "schema_name": "schema_name_val", "nested": {"SEC_ONE": "SEC_ONE_VAL"  }  } } }}

    results = extract_config_secrets(config)

    assert len(results) == 3
    assert "database_name_val" in results
    assert "schema_name_val" in results
    assert "SEC_ONE_VAL" in results


def test_extract_config_secrets_given__vars_with_same_secret_twice_then_only_extracted_once():
    config = {"vars": {"secrets" : {"database_name": "SECRET_VALUE", "schema_name": "SECRET_VALUE", "nested_secrets": {"SEC_ONE": "SECRET_VALUE"  } } }}

    results = extract_config_secrets(config)

    assert len(results) == 1
    assert "SECRET_VALUE" in results
