from __future__ import annotations

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
    assert (
        str(e.value)
        == "Could not find environmental variable SF_DATABASE and no default value was provided"
    )


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
