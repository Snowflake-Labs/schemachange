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


def test_multiline_secret_stores_multiple_representations():
    """Test that multi-line secrets are stored in multiple formats - fixes issue #237"""
    config_vars = {"secrets": {"azure_ad_certificate": "foobarfoobarfoobar\nfoobarfoobarfoobar"}}

    results = get_config_secrets(config_vars)

    # Should store multiple representations for redaction to work with different serialization formats
    assert "foobarfoobarfoobar\nfoobarfoobarfoobar" in results  # Original
    assert "foobarfoobarfoobar\nfoobarfoobarfoobar" in results  # Stripped (same in this case)
    assert "foobarfoobarfoobar foobarfoobarfoobar" in results  # Normalized (newline -> space)
    assert "foobarfoobarfoobar" in results  # Individual lines


def test_multiline_secret_with_indentation_stores_all_variants():
    """Test that multi-line secrets with indentation are properly extracted - issue #237"""
    config_vars = {"secrets": {"multiline_key": "  line1\n  line2\n  line3"}}

    results = get_config_secrets(config_vars)

    # Original with indentation
    assert "  line1\n  line2\n  line3" in results
    # Stripped version
    assert "line1\n  line2\n  line3" in results
    # Normalized
    assert "line1 line2 line3" in results
    # Individual lines stripped
    assert "line1" in results
    assert "line2" in results
    assert "line3" in results


def test_multiline_secret_with_yaml_literal_block_style():
    """Test multi-line secret as it would come from YAML |- block style - issue #237"""
    # This is how YAML parses: |-
    #   foobarfoobarfoobar
    #   foobarfoobarfoobar
    config_vars = {"secrets": {"azure_ad_certificate": "foobarfoobarfoobar\nfoobarfoobarfoobar"}}

    results = get_config_secrets(config_vars)

    # All these should be in results to handle different display formats
    assert len(results) >= 3  # At least: original, normalized, and individual lines
    assert "foobarfoobarfoobar" in results  # Individual line
    assert "foobarfoobarfoobar foobarfoobarfoobar" in results  # Normalized


def test_single_line_secret_still_works():
    """Test that single-line secrets still work correctly after multi-line fix - issue #237"""
    config_vars = {"secrets": {"simple_secret": "simple_value"}}

    results = get_config_secrets(config_vars)

    # Single-line secrets should store original and stripped (same in this case)
    assert "simple_value" in results
    # Should not create extra entries for single-line secrets
    assert all("simple_value" in s for s in results if s)  # All results should be the value


def test_empty_lines_in_multiline_secret_are_handled():
    """Test that empty lines in multi-line secrets don't create empty string entries - issue #237"""
    config_vars = {"secrets": {"cert_with_empty_lines": "line1\n\nline2\n\n\nline3"}}

    results = get_config_secrets(config_vars)

    # Should not contain empty strings
    assert "" not in results
    # Should contain individual lines
    assert "line1" in results
    assert "line2" in results
    assert "line3" in results
