import pytest
import schemachange.cli


def test_alphanum_convert_integer():
    assert schemachange.cli.alphanum_convert("123") == 123


def test_alphanum_convert_lowercase():
    assert schemachange.cli.alphanum_convert("TEST") == "test"


def test_get_alphanum_key_empty_string():
    assert schemachange.cli.get_alphanum_key("") == [""]


def test_get_alphanum_key_numbers_only():
    assert schemachange.cli.get_alphanum_key("123") == ["", 123, ""]


def test_get_alphanum_key_alphabets_only():
    assert schemachange.cli.get_alphanum_key("abc") == ["abc"]


def test_get_alphanum_key_upper_alphanumeric():
    assert schemachange.cli.get_alphanum_key("V1.2.3__") == [
        "v",
        1,
        ".",
        2,
        ".",
        3,
        "__",
    ]


def test_get_alphanum_key_valid_version_string():
    assert schemachange.cli.get_alphanum_key("1.2.2") == ["", 1, ".", 2, ".", 2, ""]


def test_sorted_alphanumeric_mixed_string():
    assert schemachange.cli.sorted_alphanumeric(
        ["V1.2.3__file.sql", "V1.2.4__file.sql"]
    ) == ["V1.2.3__file.sql", "V1.2.4__file.sql"]
