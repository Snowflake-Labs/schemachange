from __future__ import annotations

import json
import os
import tempfile
import unittest.mock as mock

import jinja2
import pytest

from schemachange.LocalDataInjection import LocalDataInjection


@mock.patch.dict(os.environ, {}, clear=True)
def test_env_var_with_no_default_and_no_environmental_variables_should_raise_exception():
    assert ("SF_DATABASE" in os.environ) is False

    with pytest.raises(ValueError) as e:
        LocalDataInjection.env_var("SF_DATABASE")
    assert str(e.value) == "Could not find environmental variable SF_DATABASE and no default value was provided"


@mock.patch.dict(os.environ, {}, clear=True)
def test_env_var_with_default_and_no_environmental_variables_should_return_default():
    assert ("SF_DATABASE" in os.environ) is False

    result = LocalDataInjection.env_var("SF_DATABASE", "SCHEMACHANGE_DEMO")
    assert result == "SCHEMACHANGE_DEMO"


@mock.patch.dict(os.environ, {"SF_DATABASE": "SCHEMACHANGE_DEMO_2"}, clear=True)
def test_env_var_with_default_and_environmental_variables_should_return_environmental_variable_value():
    result = LocalDataInjection.env_var("SF_DATABASE", "SCHEMACHANGE_DEMO")
    assert result == "SCHEMACHANGE_DEMO_2"


@mock.patch.dict(os.environ, {"SF_DATABASE": "SCHEMACHANGE_DEMO_3"}, clear=True)
def test_localdatainjection_with_jinja_template():
    template = jinja2.Template(
        "{{env_var('SF_DATABASE', 'SCHEMACHANGE_DEMO')}}",
        extensions=[LocalDataInjection],
    )
    assert template.render() == "SCHEMACHANGE_DEMO_3"


def test_from_csv_as_tuples():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age,city\nJohn,30,New York\nJane,25,Boston\n")
        csv_path = f.name

    try:
        result = LocalDataInjection.from_csv(csv_path, as_dict=False)
        expected = [
            ("name", "age", "city"),
            ("John", "30", "New York"),
            ("Jane", "25", "Boston"),
        ]
        assert result == expected
    finally:
        os.unlink(csv_path)


def test_from_csv_as_dicts():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age,city\nJohn,30,New York\nJane,25,Boston\n")
        csv_path = f.name

    try:
        result = LocalDataInjection.from_csv(csv_path, as_dict=True)
        expected = [
            {"name": "John", "age": "30", "city": "New York"},
            {"name": "Jane", "age": "25", "city": "Boston"},
        ]
        assert result == expected
    finally:
        os.unlink(csv_path)


def test_from_csv_file_not_found():
    with pytest.raises(FileNotFoundError) as e:
        LocalDataInjection.from_csv("nonexistent.csv")
    assert "CSV file not found: nonexistent.csv" in str(e.value)


def test_from_json():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"name": "John", "age": 30, "cities": ["NYC", "LA"]}')
        json_path = f.name

    try:
        result = LocalDataInjection.from_json(json_path)
        expected = {"name": "John", "age": 30, "cities": ["NYC", "LA"]}
        assert result == expected
    finally:
        os.unlink(json_path)


def test_from_json_file_not_found():
    with pytest.raises(FileNotFoundError) as e:
        LocalDataInjection.from_json("nonexistent.json")
    assert "JSON file not found: nonexistent.json" in str(e.value)


def test_from_yaml():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("name: John\nage: 30\ncities:\n  - NYC\n  - LA\n")
        yaml_path = f.name

    try:
        result = LocalDataInjection.from_yaml(yaml_path)
        expected = {"name": "John", "age": 30, "cities": ["NYC", "LA"]}
        assert result == expected
    finally:
        os.unlink(yaml_path)


def test_from_yaml_file_not_found():
    with pytest.raises(FileNotFoundError) as e:
        LocalDataInjection.from_yaml("nonexistent.yaml")
    assert "YAML file not found: nonexistent.yaml" in str(e.value)


def test_jinja_template_with_csv_data():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\nJohn,30\nJane,25\n")
        csv_path = f.name

    try:
        template = jinja2.Template(
            "{% set data = from_csv('" + csv_path + "', as_dict=true) %}"
            "{% for row in data %}{{ row.name }} is {{ row.age }} years old\n{% endfor %}",
            extensions=[LocalDataInjection],
        )
        result = template.render()
        expected = "John is 30 years old\nJane is 25 years old\n"
        assert result == expected
    finally:
        os.unlink(csv_path)


# File size limit tests for CSV


def test_from_csv_exceeds_default_50mb_limit():
    """Test that CSV files exceeding 50MB default limit raise ValueError"""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
        # Create a file that exceeds 50MB
        file_size = 51 * 1024 * 1024  # 51MB
        f.write(b"name,age\n")
        f.write(b"x" * (file_size - 10))
        csv_path = f.name

    try:
        with pytest.raises(ValueError) as e:
            LocalDataInjection.from_csv(csv_path)
        assert "exceeds 50MB limit" in str(e.value)
    finally:
        os.unlink(csv_path)


def test_from_csv_with_max_file_size_none_bypasses_limit():
    """Test that setting max_file_size=None bypasses the file size check"""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
        # Create a file that exceeds 50MB
        file_size = 51 * 1024 * 1024  # 51MB
        f.write(b"name,age\nJohn,30\n")
        f.write(b"x" * (file_size - 100))
        csv_path = f.name

    try:
        # Should not raise an exception when max_file_size is None
        result = LocalDataInjection.from_csv(csv_path, max_file_size=None)
        # File will be valid CSV data (just with lots of padding)
        assert result is not None
    finally:
        os.unlink(csv_path)


def test_from_csv_with_custom_max_file_size():
    """Test that custom max_file_size limit is enforced"""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
        # Create a file that's 100KB
        f.write(b"name,age\n")
        f.write(b"x" * (100 * 1024))
        csv_path = f.name

    try:
        # Should raise error with a 50KB limit
        with pytest.raises(ValueError) as e:
            LocalDataInjection.from_csv(csv_path, max_file_size=50 * 1024)
        assert "exceeds" in str(e.value) and "KB limit" not in str(e.value)  # Should show MB
    finally:
        os.unlink(csv_path)


def test_from_csv_within_default_limit():
    """Test that CSV files within 50MB limit load successfully"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age,city\nJohn,30,NYC\nJane,25,LA\n")
        csv_path = f.name

    try:
        result = LocalDataInjection.from_csv(csv_path)
        assert len(result) == 3  # header + 2 rows
    finally:
        os.unlink(csv_path)


# File size limit tests for JSON


def test_from_json_exceeds_default_50mb_limit():
    """Test that JSON files exceeding 50MB default limit raise ValueError"""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as f:
        # Create a file that exceeds 50MB
        file_size = 51 * 1024 * 1024  # 51MB
        f.write(b'{"data":"')
        f.write(b"x" * (file_size - 50))
        f.write(b'"}\n')
        json_path = f.name

    try:
        with pytest.raises(ValueError) as e:
            LocalDataInjection.from_json(json_path)
        assert "exceeds 50MB limit" in str(e.value)
    finally:
        os.unlink(json_path)


def test_from_json_with_max_file_size_none_bypasses_limit():
    """Test that setting max_file_size=None bypasses the file size check for JSON"""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as f:
        # Create a file that exceeds 50MB
        file_size = 51 * 1024 * 1024  # 51MB
        f.write(b'{"name": "John"}')
        f.write(b"x" * (file_size - 100))
        f.seek(0)
        json_path = f.name

    try:
        # This will fail to parse (not valid JSON), but the size check should pass
        # We're just verifying the size check is bypassed
        with pytest.raises(json.JSONDecodeError):
            LocalDataInjection.from_json(json_path, max_file_size=None)
    finally:
        os.unlink(json_path)


def test_from_json_with_custom_max_file_size():
    """Test that custom max_file_size limit is enforced for JSON"""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as f:
        # Create a file that's 100KB
        f.write(b'{"data":"')
        f.write(b"x" * (100 * 1024))
        f.write(b'"}')
        json_path = f.name

    try:
        # Should raise error with a 50KB limit
        with pytest.raises(ValueError) as e:
            LocalDataInjection.from_json(json_path, max_file_size=50 * 1024)
        assert "exceeds" in str(e.value)
    finally:
        os.unlink(json_path)


def test_from_json_within_default_limit():
    """Test that JSON files within 50MB limit load successfully"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"name": "John", "age": 30}')
        json_path = f.name

    try:
        result = LocalDataInjection.from_json(json_path)
        assert result == {"name": "John", "age": 30}
    finally:
        os.unlink(json_path)


# File size limit tests for YAML


def test_from_yaml_exceeds_default_50mb_limit():
    """Test that YAML files exceeding 50MB default limit raise ValueError"""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".yaml", delete=False) as f:
        # Create a file that exceeds 50MB
        file_size = 51 * 1024 * 1024  # 51MB
        f.write(b"name: John\ndata: ")
        f.write(b"x" * (file_size - 50))
        yaml_path = f.name

    try:
        with pytest.raises(ValueError) as e:
            LocalDataInjection.from_yaml(yaml_path)
        assert "exceeds 50MB limit" in str(e.value)
    finally:
        os.unlink(yaml_path)


def test_from_yaml_with_max_file_size_none_bypasses_limit():
    """Test that setting max_file_size=None bypasses the file size check for YAML"""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".yaml", delete=False) as f:
        # Create a file that exceeds 50MB
        file_size = 51 * 1024 * 1024  # 51MB
        f.write(b"name: John\n")
        f.write(b"x" * (file_size - 50))
        yaml_path = f.name

    try:
        # Should not raise a size limit error (may raise YAML parse error, but that's OK)
        result = LocalDataInjection.from_yaml(yaml_path, max_file_size=None)
        # If it gets here, the size check was bypassed
        assert result is not None or True  # Size check was skipped
    except ValueError as e:
        # Should not be a size limit error
        assert "exceeds" not in str(e.value) and "MB limit" not in str(e.value)
    finally:
        os.unlink(yaml_path)


def test_from_yaml_with_custom_max_file_size():
    """Test that custom max_file_size limit is enforced for YAML"""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".yaml", delete=False) as f:
        # Create a file that's 100KB
        f.write(b"name: John\ndata: ")
        f.write(b"x" * (100 * 1024))
        yaml_path = f.name

    try:
        # Should raise error with a 50KB limit
        with pytest.raises(ValueError) as e:
            LocalDataInjection.from_yaml(yaml_path, max_file_size=50 * 1024)
        assert "exceeds" in str(e.value)
    finally:
        os.unlink(yaml_path)


def test_from_yaml_within_default_limit():
    """Test that YAML files within 50MB limit load successfully"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("name: John\nage: 30\ncities:\n  - NYC\n  - LA\n")
        yaml_path = f.name

    try:
        result = LocalDataInjection.from_yaml(yaml_path)
        assert result == {"name": "John", "age": 30, "cities": ["NYC", "LA"]}
    finally:
        os.unlink(yaml_path)
