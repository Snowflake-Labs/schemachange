from __future__ import annotations

from pathlib import Path

import pytest

from schemachange.session.Script import (
    AlwaysScript,
    RepeatableScript,
    Script,
    VersionedScript,
    get_all_scripts_recursively,
    script_factory,
)


class TestScript:
    @pytest.mark.parametrize(
        "file_path, expected",
        [
            (Path("nested/file/V123__something.sql.jinja"), "V123__something.sql"),
            (Path("nested/file/R__something.sql.jinja"), "R__something.sql"),
            (Path("nested/file/A__something.sql.jinja"), "A__something.sql"),
            (Path("nested/file/V123__something.sql"), "V123__something.sql"),
            (Path("nested/file/R__something.sql"), "R__something.sql"),
            (Path("nested/file/A__something.sql"), "A__something.sql"),
        ],
    )
    def test_get_script_name(self, file_path: Path, expected: str):
        result = Script.get_script_name(file_path)
        assert result == expected

    @pytest.mark.parametrize(
        "file_path, expected",
        [
            (
                Path("nested/file/V123__something.sql.jinja"),
                VersionedScript(
                    name="V123__something.sql",
                    file_path=Path("nested/file/V123__something.sql.jinja"),
                    description="Something",
                    version="123",
                ),
            ),
            (
                Path("nested/file/V1.2.3__something.sql.jinja"),
                VersionedScript(
                    name="V1.2.3__something.sql",
                    file_path=Path("nested/file/V1.2.3__something.sql.jinja"),
                    description="Something",
                    version="1.2.3",
                ),
            ),
            (
                Path("nested/file/V1_2_3__something.sql.jinja"),
                VersionedScript(
                    name="V1_2_3__something.sql",
                    file_path=Path("nested/file/V1_2_3__something.sql.jinja"),
                    description="Something",
                    version="1_2_3",
                ),
            ),
            (
                Path("nested/file/R__something.sql.jinja"),
                RepeatableScript(
                    name="R__something.sql",
                    file_path=Path("nested/file/R__something.sql.jinja"),
                    description="Something",
                ),
            ),
            (
                Path("nested/file/A__something.sql.jinja"),
                AlwaysScript(
                    name="A__something.sql",
                    file_path=Path("nested/file/A__something.sql.jinja"),
                    description="Something",
                ),
            ),
            (
                Path("nested/file/V123__something.sql"),
                VersionedScript(
                    name="V123__something.sql",
                    file_path=Path("nested/file/V123__something.sql"),
                    description="Something",
                    version="123",
                ),
            ),
            (
                Path("nested/file/V1_2_3__something.sql"),
                VersionedScript(
                    name="V1_2_3__something.sql",
                    file_path=Path("nested/file/V1_2_3__something.sql"),
                    description="Something",
                    version="1_2_3",
                ),
            ),
            (
                Path("nested/file/V1.2.3__something.sql"),
                VersionedScript(
                    name="V1.2.3__something.sql",
                    file_path=Path("nested/file/V1.2.3__something.sql"),
                    description="Something",
                    version="1.2.3",
                ),
            ),
            (
                Path("nested/file/R__something.sql"),
                RepeatableScript(
                    name="R__something.sql",
                    file_path=Path("nested/file/R__something.sql"),
                    description="Something",
                ),
            ),
            (
                Path("nested/file/A__something.sql"),
                AlwaysScript(
                    name="A__something.sql",
                    file_path=Path("nested/file/A__something.sql"),
                    description="Something",
                ),
            ),
            (Path("nested/file/something.sql"), None),
            (Path("nested/file/something.sql.jinja"), None),
            (
                Path("nested/file/A__a_longer_name.sql"),
                AlwaysScript(
                    name="A__a_longer_name.sql",
                    file_path=Path("nested/file/A__a_longer_name.sql"),
                    description="A longer name",
                ),
            ),
        ],
    )
    def test_script_factory(self, file_path: Path, expected: Script):
        result = script_factory(file_path)
        assert result == expected

    @pytest.mark.parametrize(
        "file_path",
        [
            (Path("nested/file/V123_something.sql.jinja")),
            (Path("nested/file/V1_2_3_something.sql.jinja")),
            (Path("nested/file/V1.2.3_something.sql.jinja")),
            (Path("nested/file/R_something.sql.jinja")),
            (Path("nested/file/A_something.sql.jinja")),
        ],
    )
    def test_single_underscore_should_raise_exception(self, file_path: Path):
        with pytest.raises(ValueError) as e:
            script_factory(file_path)
        assert str(file_path) in str(e.value) and "two underscores" in str(e.value)

    def test_missing_version_should_raise_exception(self):
        file_path = Path("nested/file/V__something.sql.jinja")
        with pytest.raises(ValueError) as e:
            script_factory(file_path)
        assert str(file_path) in str(e.value) and "Versioned migrations must be prefixed with a version" in str(e.value)


class TestGetAllScriptsRecursively:
    def test_given_empty_folder_should_return_empty(self, fs):
        root_directory = Path("some_path")
        result = get_all_scripts_recursively(root_directory)

        assert result == {}

    def test_given_just_non_change_files_should_return_empty(self, fs):
        fs.create_file(Path("scripts") / "README.txt")
        fs.create_file(Path("scripts") / "subfolder" / "subfolder2" / "something.sql")
        fs.create_file(Path("scripts") / "subfolder" / "subfolder2" / "testing.py")
        result = get_all_scripts_recursively(Path("scripts"))

        assert result == {}

    ############################
    #### Version file tests ####
    ############################

    def test_version_number_regex_numeric_happy_path(self, fs):
        fs.create_file(Path("scripts") / "V1.1.1__initial.sql")
        fs.create_file(Path("scripts") / "subfolder" / "V1.1.2__update.SQL")
        fs.create_file(Path("scripts") / "subfolder" / "subfolder2" / "V1.1.3__update.sql")

        result = get_all_scripts_recursively(
            Path("scripts"),
            version_number_regex=r"\d\.\d\.\d",  # noqa: W605
        )

        assert len(result) == 3
        assert "v1.1.1__initial.sql" in result
        assert "v1.1.2__update.sql" in result
        assert "v1.1.3__update.sql" in result

    def test_version_number_regex_numeric_exception(self, fs):
        fs.create_file(Path("scripts") / "V1.10.1__initial.sql")
        with pytest.raises(ValueError) as e:
            get_all_scripts_recursively(
                Path("scripts"),
                version_number_regex=r"\d\.\d\.\d",  # noqa: W605
            )
        assert str(e.value).startswith("change script version doesn't match the supplied regular expression")

    def test_version_number_regex_text_happy_path(self, fs):
        fs.create_file(Path("scripts") / "Va.b.c__initial.sql")

        result = get_all_scripts_recursively(
            Path("scripts"),
            version_number_regex=r"[a-z]\.[a-z]\.[a-z]",  # noqa: W605
        )
        assert len(result) == 1
        assert "va.b.c__initial.sql" in result

    def test_version_number_regex_text_exception(self, fs):
        fs.create_file(Path("scripts") / "V1.10.1__initial.sql")
        with pytest.raises(ValueError) as e:
            get_all_scripts_recursively(
                Path("scripts"),
                version_number_regex=r"[a-z]\.[a-z]\.[a-z]",  # noqa: W605
            )
        assert str(e.value).startswith("change script version doesn't match the supplied regular expression")

    def test_given_version_files_should_return_version_files(self, fs):
        fs.create_file(Path("scripts") / "V1.1.1__initial.sql")
        fs.create_file(Path("scripts") / "subfolder" / "V1.1.2__update.SQL")
        fs.create_file(Path("scripts") / "subfolder" / "subfolder2" / "V1.1.3__update.sql")
        result = get_all_scripts_recursively(Path("scripts"))

        assert len(result) == 3
        assert "v1.1.1__initial.sql" in result
        assert "v1.1.2__update.sql" in result
        assert "v1.1.3__update.sql" in result

    def test_given_same_version_twice_should_raise_exception(self, fs):
        fs.create_file(Path("scripts") / "V1.1.1__initial.sql")
        fs.create_file(Path("scripts") / "subfolder" / "V1.1.1__update.sql")
        fs.create_file(Path("scripts") / "subfolder" / "subfolder2" / "V1.1.2__update.sql")

        with pytest.raises(ValueError) as e:
            get_all_scripts_recursively(Path("scripts"))
        assert str(e.value).startswith("The script version 1.1.1 exists more than once (second instance")

    def test_given_single_version_file_should_extract_attributes(self, fs):
        fs.create_file(Path("scripts") / "subfolder" / "V1.1.1.1__THIS_is_my_test.sql")

        result = get_all_scripts_recursively(Path("scripts"))

        assert len(result) == 1
        script = result["v1.1.1.1__this_is_my_test.sql"]
        assert script.name == "V1.1.1.1__THIS_is_my_test.sql"
        assert script.file_path == Path("scripts") / "subfolder" / "V1.1.1.1__THIS_is_my_test.sql"
        assert script.type == "V"
        assert script.version == "1.1.1.1"
        assert script.description == "This is my test"

    def test_given_single_version_jinja_file_should_extract_attributes(self, fs):
        fs.create_file(Path("scripts") / "subfolder" / "V1.1.1.2__THIS_is_my_test.sql.jinja")

        result = get_all_scripts_recursively(Path("scripts"))

        assert len(result) == 1
        script = result["v1.1.1.2__this_is_my_test.sql"]
        assert script.name == "V1.1.1.2__THIS_is_my_test.sql"
        assert script.file_path == Path("scripts") / "subfolder" / "V1.1.1.2__THIS_is_my_test.sql.jinja"
        assert script.type == "V"
        assert script.version == "1.1.1.2"
        assert script.description == "This is my test"

    def test_given_same_version_file_with_and_without_jinja_extension_should_raise_exception(self, fs):
        fs.create_file(Path("scripts") / "V1.1.1__initial.sql")
        fs.create_file(Path("scripts") / "V1.1.1__initial.sql.jinja")
        with pytest.raises(ValueError) as e:
            get_all_scripts_recursively(Path("scripts"))
        assert str(e.value).startswith("The script name V1.1.1__initial.sql exists more than once (first_instance")

    ###########################
    #### Always file tests ####
    ###########################

    def test_given_always_files_should_return_always_files(self, fs):
        fs.create_file(Path("scripts") / "A__proc1.sql")
        fs.create_file(Path("scripts") / "subfolder" / "A__proc2.SQL")
        fs.create_file(Path("scripts") / "subfolder" / "subfolder2" / "A__proc3.sql")

        result = get_all_scripts_recursively(Path("scripts"))

        assert len(result) == 3
        assert "a__proc1.sql" in result
        assert "a__proc2.sql" in result
        assert "a__proc3.sql" in result

    def test_given_same_always_file_should_raise_exception(self, fs):
        fs.create_file(Path("scripts") / "A__initial.sql")
        fs.create_file(Path("scripts") / "subfolder" / "A__initial.sql")
        fs.create_file(Path("scripts") / "subfolder" / "subfolder2" / "A__proc3.sql")

        with pytest.raises(ValueError) as e:
            get_all_scripts_recursively(Path("scripts"))
        assert str(e.value).startswith("The script name A__initial.sql exists more than once (first_instance ")

    def test_given_single_always_file_should_extract_attributes(self, fs):
        fs.create_file(Path("scripts") / "subfolder" / "A__THIS_is_my_test.sql")
        result = get_all_scripts_recursively(Path("scripts"))

        assert len(result) == 1
        script = result["a__this_is_my_test.sql"]
        assert script.name == "A__THIS_is_my_test.sql"
        assert script.file_path == Path("scripts") / "subfolder" / "A__THIS_is_my_test.sql"
        assert script.type == "A"
        assert script.description == "This is my test"

    def test_given_single_always_jinja_file_should_extract_attributes(self, fs):
        fs.create_file(Path("scripts") / "subfolder" / "A__THIS_is_my_test.sql.jinja")
        result = get_all_scripts_recursively(Path("scripts"))

        assert len(result) == 1
        script = result["a__this_is_my_test.sql"]
        assert script.name == "A__THIS_is_my_test.sql"
        assert script.file_path == Path("scripts") / "subfolder" / "A__THIS_is_my_test.sql.jinja"
        assert script.type == "A"
        assert script.description == "This is my test"

    def test_given_same_always_file_with_and_without_jinja_extension_should_raise_exception(self, fs):
        fs.create_file(Path("scripts") / "A__initial.sql")
        fs.create_file(Path("scripts") / "A__initial.sql.jinja")

        with pytest.raises(ValueError) as e:
            get_all_scripts_recursively(Path("scripts"))
        assert str(e.value).startswith("The script name A__initial.sql exists more than once (first_instance ")

    ###############################
    #### Repeatable file tests ####
    ###############################

    def test_given_repeatable_files_should_return_repeatable_files(self, fs):
        fs.create_file(Path("scripts") / "R__proc1.sql")
        fs.create_file(Path("scripts") / "subfolder" / "R__proc2.SQL")
        fs.create_file(Path("scripts") / "subfolder" / "subfolder2" / "R__proc3.sql")
        result = get_all_scripts_recursively(Path("scripts"))

        assert len(result) == 3
        assert "r__proc1.sql" in result
        assert "r__proc2.sql" in result
        assert "r__proc3.sql" in result

    def test_given_same_repeatable_file_should_raise_exception(self, fs):
        fs.create_file(Path("scripts") / "R__initial.sql")
        fs.create_file(Path("scripts") / "subfolder" / "R__initial.SQL")
        with pytest.raises(ValueError) as e:
            get_all_scripts_recursively(Path("scripts"))
        assert str(e.value).startswith("The script name R__initial.SQL exists more than once (first_instance ")

    def test_given_single_repeatable_file_should_extract_attributes(self, fs):
        fs.create_file(Path("scripts") / "subfolder" / "R__THIS_is_my_test.sql")
        result = get_all_scripts_recursively(Path("scripts"))

        assert len(result) == 1
        script = result["r__this_is_my_test.sql"]
        assert script.name == "R__THIS_is_my_test.sql"
        assert script.file_path == Path("scripts") / "subfolder" / "R__THIS_is_my_test.sql"
        assert script.type == "R"
        assert script.description == "This is my test"

    def test_given_single_repeatable_jinja_file_should_extract_attributes(self, fs):
        fs.create_file(Path("scripts") / "subfolder" / "R__THIS_is_my_test.sql.jinja")
        result = get_all_scripts_recursively(Path("scripts"))

        assert len(result) == 1
        script = result["r__this_is_my_test.sql"]
        assert script.name == "R__THIS_is_my_test.sql"
        assert script.file_path == Path("scripts") / "subfolder" / "R__THIS_is_my_test.sql.jinja"
        assert script.type == "R"
        assert script.description == "This is my test"

    def test_given_same_repeatable_file_with_and_without_jinja_extension_should_raise_exception(self, fs):
        fs.create_file(Path("scripts") / "R__initial.sql")
        fs.create_file(Path("scripts") / "R__initial.sql.jinja")
        with pytest.raises(ValueError) as e:
            get_all_scripts_recursively(Path("scripts"))
        assert str(e.value).startswith("The script name R__initial.sql exists more than once (first_instance ")
