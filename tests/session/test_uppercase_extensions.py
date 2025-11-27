"""Test that uppercase .SQL extensions are detected correctly."""

from schemachange.session.Script import get_all_scripts_recursively


class TestUppercaseExtensions:
    """Test uppercase file extension support."""

    def test_uppercase_sql_extensions_detected(self, tmp_path):
        """Verify that .SQL (uppercase) files are detected."""
        # Create test files with uppercase extensions
        (tmp_path / "V1.0.0__test.SQL").write_text("SELECT 1;")
        (tmp_path / "R__repeatable.SQL").write_text("SELECT 2;")
        (tmp_path / "A__always.SQL").write_text("SELECT 3;")

        # Get all scripts
        scripts = get_all_scripts_recursively(tmp_path)

        # Verify all three scripts were detected
        assert len(scripts) == 3
        assert "v1.0.0__test.sql" in scripts  # Stored in lowercase
        assert "r__repeatable.sql" in scripts
        assert "a__always.sql" in scripts

    def test_mixed_case_sql_extensions_detected(self, tmp_path):
        """Verify that .Sql (mixed case) files are detected."""
        (tmp_path / "V1.0.0__test.Sql").write_text("SELECT 1;")

        scripts = get_all_scripts_recursively(tmp_path)

        assert len(scripts) == 1
        assert "v1.0.0__test.sql" in scripts

    def test_lowercase_sql_extensions_detected(self, tmp_path):
        """Verify that .sql (lowercase) files still work."""
        (tmp_path / "V1.0.0__test.sql").write_text("SELECT 1;")

        scripts = get_all_scripts_recursively(tmp_path)

        assert len(scripts) == 1
        assert "v1.0.0__test.sql" in scripts

    def test_uppercase_jinja_extensions_detected(self, tmp_path):
        """Verify that .SQL.JINJA (uppercase) files are detected."""
        (tmp_path / "V1.0.0__test.SQL.JINJA").write_text("SELECT 1;")
        (tmp_path / "R__repeatable.sql.Jinja").write_text("SELECT 2;")

        scripts = get_all_scripts_recursively(tmp_path)

        assert len(scripts) == 2
        # Jinja extension is stripped, leaving just the base name
        assert "v1.0.0__test.sql" in scripts
        assert "r__repeatable.sql" in scripts

    def test_case_insensitive_extension_matching(self, tmp_path):
        """Verify case-insensitive pattern matching works for various cases."""
        test_cases = [
            "V1.0.0__test.sql",
            "V2.0.0__test.SQL",
            "V3.0.0__test.Sql",
            "V4.0.0__test.sQl",
            "V5.0.0__test.SqL",
        ]

        for filename in test_cases:
            (tmp_path / filename).write_text("SELECT 1;")

        scripts = get_all_scripts_recursively(tmp_path)

        # All files should be detected
        assert len(scripts) == len(test_cases)
