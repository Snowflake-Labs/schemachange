import os
import unittest.mock as mock

import pytest

from schemachange.cli import get_all_scripts_recursively

#######################
#### Generic tests ####
#######################


def test_get_all_scripts_recursively__given_empty_folder_should_return_empty():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = []
        result = get_all_scripts_recursively("scripts", False)

    assert result == dict()


def test_get_all_scripts_recursively__given_just_non_change_files_should_return_empty():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("", ("subfolder"), ("README.txt",)),
            ("subfolder", ("subfolder2"), ("something.sql",)),
            (f"subfolder{os.sep}subfolder2", (""), ("testing.py",)),
        ]
        result = get_all_scripts_recursively("scripts", False)

    assert result == dict()


############################
#### Version file tests ####
############################


def test_get_all_scripts_recursively__given_Version_files_should_return_version_files():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("", ("subfolder"), ("V1.1.1__intial.sql",)),
            ("subfolder", ("subfolder2"), ("V1.1.2__update.SQL",)),
            (f"subfolder{os.sep}subfolder2", (""), ("V1.1.3__update.sql",)),
        ]

        result = get_all_scripts_recursively("scripts", False)

    assert len(result) == 3
    assert "V1.1.1__intial.sql" in result
    assert "V1.1.2__update.SQL" in result
    assert "V1.1.3__update.sql" in result


def test_get_all_scripts_recursively__given_same_Version_twice_should_raise_exception():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("", ("subfolder"), ("V1.1.1__intial.sql",)),
            ("subfolder", ("subfolder2"), ("V1.1.1__update.sql",)),
            (f"subfolder{os.sep}subfolder2", (""), ("V1.1.2__update.sql",)),
        ]

        with pytest.raises(ValueError) as e:
            result = get_all_scripts_recursively("scripts", False)
        assert str(e.value).startswith(
            "The script version 1.1.1 exists more than once (second instance"
        )


def test_get_all_scripts_recursively__given_single_Version_file_should_extract_attributes():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("subfolder", (), ("V1.1.1.1__THIS_is_my_test.sql",)),
        ]
        result = get_all_scripts_recursively("scripts", False)

    assert len(result) == 1
    file_attributes = result["V1.1.1.1__THIS_is_my_test.sql"]
    assert file_attributes["script_name"] == "V1.1.1.1__THIS_is_my_test.sql"
    assert file_attributes["script_full_path"] == os.path.join(
        "subfolder", "V1.1.1.1__THIS_is_my_test.sql"
    )
    assert file_attributes["script_type"] == "V"
    assert file_attributes["script_version"] == "1.1.1.1"
    assert file_attributes["script_description"] == "This is my test"


def test_get_all_scripts_recursively__given_single_Version_jinja_file_should_extract_attributes():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("subfolder", (), ("V1.1.1.2__THIS_is_my_test.sql.jinja",)),
        ]
        result = get_all_scripts_recursively("scripts", False)

    assert len(result) == 1
    file_attributes = result["V1.1.1.2__THIS_is_my_test.sql"]
    assert file_attributes["script_name"] == "V1.1.1.2__THIS_is_my_test.sql"
    assert file_attributes["script_full_path"] == os.path.join(
        "subfolder", "V1.1.1.2__THIS_is_my_test.sql.jinja"
    )
    assert file_attributes["script_type"] == "V"
    assert file_attributes["script_version"] == "1.1.1.2"
    assert file_attributes["script_description"] == "This is my test"


def test_get_all_scripts_recursively__given_same_version_file_with_and_without_jinja_extension_should_raise_exception():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("", (""), ("V1.1.1__intial.sql", "V1.1.1__intial.sql.jinja")),
        ]

        with pytest.raises(ValueError) as e:
            result = get_all_scripts_recursively("scripts", False)
        assert str(e.value).startswith(
            "The script name V1.1.1__intial.sql exists more than once (first_instance"
        )


###########################
#### Always file tests ####
###########################


def test_get_all_scripts_recursively__given_Always_files_should_return_always_files():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("", ("subfolder"), ("A__proc1.sql",)),
            ("subfolder", ("subfolder2"), ("A__proc2.SQL",)),
            (f"subfolder{os.sep}subfolder2", (""), ("A__proc3.sql",)),
        ]

        result = get_all_scripts_recursively("scripts", False)

    assert len(result) == 3
    assert "A__proc1.sql" in result
    assert "A__proc2.SQL" in result
    assert "A__proc3.sql" in result


def test_get_all_scripts_recursively__given_same_Always_file_should_raise_exception():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("", ("subfolder"), ("A__intial.sql",)),
            ("subfolder", (), ("A__intial.sql",)),
        ]

        with pytest.raises(ValueError) as e:
            result = get_all_scripts_recursively("scripts", False)
        assert str(e.value).startswith(
            "The script name A__intial.sql exists more than once (first_instance "
        )


def test_get_all_scripts_recursively__given_single_Always_file_should_extract_attributes():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("subfolder", (), ("A__THIS_is_my_test.sql",)),
        ]
        result = get_all_scripts_recursively("scripts", False)

    assert len(result) == 1
    file_attributes = result["A__THIS_is_my_test.sql"]
    assert file_attributes["script_name"] == "A__THIS_is_my_test.sql"
    assert file_attributes["script_full_path"] == os.path.join(
        "subfolder", "A__THIS_is_my_test.sql"
    )
    assert file_attributes["script_type"] == "A"
    assert file_attributes["script_version"] == ""
    assert file_attributes["script_description"] == "This is my test"


def test_get_all_scripts_recursively__given_single_Always_jinja_file_should_extract_attributes():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("subfolder", (), ("A__THIS_is_my_test.sql.jinja",)),
        ]
        result = get_all_scripts_recursively("scripts", False)

    assert len(result) == 1
    file_attributes = result["A__THIS_is_my_test.sql"]
    assert file_attributes["script_name"] == "A__THIS_is_my_test.sql"
    assert file_attributes["script_full_path"] == os.path.join(
        "subfolder", "A__THIS_is_my_test.sql.jinja"
    )
    assert file_attributes["script_type"] == "A"
    assert file_attributes["script_version"] == ""
    assert file_attributes["script_description"] == "This is my test"


def test_get_all_scripts_recursively__given_same_Always_file_with_and_without_jinja_extension_should_raise_exception():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("", (""), ("A__intial.sql", "A__intial.sql.jinja")),
        ]

        with pytest.raises(ValueError) as e:
            result = get_all_scripts_recursively("scripts", False)
        assert str(e.value).startswith(
            "The script name A__intial.sql exists more than once (first_instance "
        )


###############################
#### Repeatable file tests ####
###############################


def test_get_all_scripts_recursively__given_Repeatable_files_should_return_repeatable_files():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("", ("subfolder"), ("R__proc1.sql",)),
            ("subfolder", ("subfolder2"), ("R__proc2.SQL",)),
            (f"subfolder{os.sep}subfolder2", (), ("R__proc3.sql",)),
        ]

        result = get_all_scripts_recursively("scripts", False)

    assert len(result) == 3
    assert "R__proc1.sql" in result
    assert "R__proc2.SQL" in result
    assert "R__proc3.sql" in result


def test_get_all_scripts_recursively__given_same_Repeatable_file_should_raise_exception():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("", ("subfolder"), ("R__intial.sql",)),
            ("subfolder", (), ("R__intial.sql",)),
        ]

        with pytest.raises(ValueError) as e:
            result = get_all_scripts_recursively("scripts", False)
        assert str(e.value).startswith(
            "The script name R__intial.sql exists more than once (first_instance "
        )


def test_get_all_scripts_recursively__given_single_Repeatable_file_should_extract_attributes():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("subfolder", (), ("R__THIS_is_my_test.sql",)),
        ]
        result = get_all_scripts_recursively("scripts", False)

    assert len(result) == 1
    file_attributes = result["R__THIS_is_my_test.sql"]
    assert file_attributes["script_name"] == "R__THIS_is_my_test.sql"
    assert file_attributes["script_full_path"] == os.path.join(
        "subfolder", "R__THIS_is_my_test.sql"
    )
    assert file_attributes["script_type"] == "R"
    assert file_attributes["script_version"] == ""
    assert file_attributes["script_description"] == "This is my test"


def test_get_all_scripts_recursively__given_single_Repeatable_jinja_file_should_extract_attributes():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("subfolder", (), ("R__THIS_is_my_test.sql.jinja",)),
        ]
        result = get_all_scripts_recursively("scripts", False)

    assert len(result) == 1
    file_attributes = result["R__THIS_is_my_test.sql"]
    assert file_attributes["script_name"] == "R__THIS_is_my_test.sql"
    assert file_attributes["script_full_path"] == os.path.join(
        "subfolder", "R__THIS_is_my_test.sql.jinja"
    )
    assert file_attributes["script_type"] == "R"
    assert file_attributes["script_version"] == ""
    assert file_attributes["script_description"] == "This is my test"


def test_get_all_scripts_recursively__given_same_Repeatable_file_with_and_without_jinja_extension_should_raise_exception():
    with mock.patch("os.walk") as mockwalk:
        mockwalk.return_value = [
            ("", (""), ("R__intial.sql", "R__intial.sql.jinja")),
        ]

        with pytest.raises(ValueError) as e:
            result = get_all_scripts_recursively("scripts", False)
        assert str(e.value).startswith(
            "The script name R__intial.sql exists more than once (first_instance "
        )
