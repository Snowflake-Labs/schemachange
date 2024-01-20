import pytest

from schemachange.SecretManager import SecretManager, extract_config_secrets


##### test Class #####
class TestSecretManager:
    def test_given_no_secrets_when_redact_then_return_original_value(self):
        sm = SecretManager()
        result = sm.redact("My string")
        assert result == "My string"

    def test_given_secrets_when_redact_on_none_then_return_none(self):
        sm = SecretManager()
        sm.add("world")
        result = sm.redact(None)
        assert result is None

    def test_given_secrets_when_redact_then_return_redacted_value(self):
        sm = SecretManager()
        sm.add("world")
        result = sm.redact("Hello world!")
        assert result == "Hello *****!"

    def test_given_secrets_when_clear_then_should_hold_zero_secrets(self):
        sm = SecretManager()
        sm.add("world")
        sm.add("Hello")

        # check private variable
        assert len(sm._SecretManager__secrets) == 2

        sm.clear()

        # check private variable
        assert len(sm._SecretManager__secrets) == 0

    def test_given_one_secrets_when_add_range_with_none_then_count_should_remain_one(
        self,
    ):
        sm = SecretManager()
        sm.add("world")
        sm.add_range(None)

        assert len(sm._SecretManager__secrets) == 1

    def test_given_one_secrets_when_add_range_with_empty_set_then_count_should_remain_one(
        self,
    ):
        sm = SecretManager()
        sm.add("world")

        range = set()
        sm.add_range(range)

        assert len(sm._SecretManager__secrets) == 1

    def test_given_one_secrets_when_add_range_with_two_secrets_then_count_of_secrets_three(
        self,
    ):
        sm = SecretManager()
        sm.add("world")

        range = {"one", "two"}
        sm.add_range(range)

        # check private variable
        assert len(sm._SecretManager__secrets) == 3
        assert "world" in sm._SecretManager__secrets
        assert "one" in sm._SecretManager__secrets
        assert "two" in sm._SecretManager__secrets


class TestExtractConfigSecrets:
    def test_given_empty_config_should_not_error(self):
        extract_config_secrets(config_vars={})

    def test_given_none_should_not_error(self):
        extract_config_secrets(None)

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
    def test_given__vars_with_keys_should_extract_secret(self, config_vars, secret):
        results = extract_config_secrets(config_vars)
        assert secret in results

    def test_given_vars_with_secrets_key_then_all_children_should_be_treated_as_secrets(
        self,
    ):
        config_vars = {
            "secrets": {
                "database_name": "database_name_val",
                "schema_name": "schema_name_val",
                "nested_secrets": {"SEC_ONE": "SEC_ONE_VAL"},
            }
        }
        results = extract_config_secrets(config_vars=config_vars)

        assert len(results) == 3
        assert "database_name_val" in results
        assert "schema_name_val" in results
        assert "SEC_ONE_VAL" in results

    def test_given_vars_with_nested_secrets_key_then_all_children_should_be_treated_as_secrets(
        self,
    ):
        config_vars = {
            "nested": {
                "secrets": {
                    "database_name": "database_name_val",
                    "schema_name": "schema_name_val",
                    "nested": {"SEC_ONE": "SEC_ONE_VAL"},
                }
            }
        }

        results = extract_config_secrets(config_vars)

        assert len(results) == 3
        assert "database_name_val" in results
        assert "schema_name_val" in results
        assert "SEC_ONE_VAL" in results

    def test_given_vars_with_same_secret_twice_then_only_extracted_once(self):
        config_vars = {
            "secrets": {
                "database_name": "SECRET_VALUE",
                "schema_name": "SECRET_VALUE",
                "nested_secrets": {"SEC_ONE": "SECRET_VALUE"},
            }
        }

        results = extract_config_secrets(config_vars)

        assert len(results) == 1
        assert "SECRET_VALUE" in results
