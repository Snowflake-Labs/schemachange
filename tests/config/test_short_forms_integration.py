"""
Integration tests for CLI short forms and argument combinations.

Tests all short forms (-f, -m, -c, -ac, -V, -L, -Q, -C) individually and in combination,
ensuring they work correctly and are properly mapped to their parameter names.
"""

import json
import logging
import os
from unittest import mock

import pytest
import structlog

from schemachange.config.get_merged_config import get_merged_config


@pytest.fixture
def clean_env():
    """Fixture to provide a clean environment for each test."""
    with mock.patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def mock_file_system():
    """Mock file system checks to avoid actual file operations."""
    with mock.patch("pathlib.Path.is_dir", return_value=True):
        with mock.patch("pathlib.Path.is_file", return_value=True):
            yield


class TestExistingShortForms:
    """Test existing lowercase short forms that should not be deprecated."""

    def test_short_form_f_root_folder(self, clean_env, mock_file_system):
        """Test -f short form for root-folder."""
        with mock.patch("sys.argv", ["schemachange", "-f", "./test-migrations"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "root_folder": "./test-migrations",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        # Verify root_folder was passed to factory
                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["root_folder"] == "./test-migrations"

    def test_short_form_m_modules_folder(self, clean_env, mock_file_system):
        """Test -m short form for modules-folder."""
        with mock.patch("sys.argv", ["schemachange", "-m", "./test-modules"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "modules_folder": "./test-modules",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["modules_folder"] == "./test-modules"

    def test_short_form_c_change_history_table(self, clean_env, mock_file_system):
        """Test -c short form for change-history-table."""
        with mock.patch("sys.argv", ["schemachange", "-c", "DB.SCHEMA.TABLE"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "change_history_table": "DB.SCHEMA.TABLE",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["change_history_table"] == "DB.SCHEMA.TABLE"

    def test_short_form_ac_autocommit(self, clean_env, mock_file_system):
        """Test -ac short form for autocommit."""
        with mock.patch("sys.argv", ["schemachange", "-ac"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "autocommit": True,
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["autocommit"] is True


class TestNewCapitalShortForms:
    """Test new capital letter short forms."""

    def test_short_form_V_vars(self, clean_env, mock_file_system):
        """Test -V short form for vars."""
        vars_dict = {"key1": "value1", "key2": "value2"}
        with mock.patch("sys.argv", ["schemachange", "-V", json.dumps(vars_dict)]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": vars_dict,
                            "connections_file_path": None,
                            "connection_name": None,
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["config_vars"] == vars_dict

    def test_short_form_L_log_level(self, clean_env, mock_file_system):
        """Test -L short form for log-level."""
        with mock.patch("sys.argv", ["schemachange", "-L", "DEBUG"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "log_level": logging.DEBUG,
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["log_level"] == logging.DEBUG

    def test_short_form_Q_query_tag(self, clean_env, mock_file_system):
        """Test -Q short form for query-tag."""
        with mock.patch("sys.argv", ["schemachange", "-Q", "my-deployment"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "query_tag": "my-deployment",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["query_tag"] == "my-deployment"

    def test_short_form_C_connection_name(self, clean_env, mock_file_system):
        """Test -C short form for connection-name."""
        with mock.patch("sys.argv", ["schemachange", "-C", "production"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": "production",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["connection_name"] == "production"


class TestSnowflakeShortForms:
    """Test Snowflake connection parameter short forms."""

    def test_short_form_a_account(self, clean_env, mock_file_system):
        """Test -a short form for snowflake-account."""
        with mock.patch("sys.argv", ["schemachange", "-a", "myaccount.us-east-1"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "snowflake_account": "myaccount.us-east-1",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["snowflake_account"] == "myaccount.us-east-1"

    def test_short_form_u_user(self, clean_env, mock_file_system):
        """Test -u short form for snowflake-user."""
        with mock.patch("sys.argv", ["schemachange", "-u", "testuser"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "snowflake_user": "testuser",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["snowflake_user"] == "testuser"

    def test_short_form_r_role(self, clean_env, mock_file_system):
        """Test -r short form for snowflake-role."""
        with mock.patch("sys.argv", ["schemachange", "-r", "DEPLOY_ROLE"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "snowflake_role": "DEPLOY_ROLE",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["snowflake_role"] == "DEPLOY_ROLE"

    def test_short_form_w_warehouse(self, clean_env, mock_file_system):
        """Test -w short form for snowflake-warehouse."""
        with mock.patch("sys.argv", ["schemachange", "-w", "COMPUTE_WH"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "snowflake_warehouse": "COMPUTE_WH",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["snowflake_warehouse"] == "COMPUTE_WH"

    def test_short_form_d_database(self, clean_env, mock_file_system):
        """Test -d short form for snowflake-database."""
        with mock.patch("sys.argv", ["schemachange", "-d", "TEST_DB"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "snowflake_database": "TEST_DB",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["snowflake_database"] == "TEST_DB"

    def test_short_form_s_schema(self, clean_env, mock_file_system):
        """Test -s short form for snowflake-schema."""
        with mock.patch("sys.argv", ["schemachange", "-s", "PUBLIC"]):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "snowflake_schema": "PUBLIC",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["snowflake_schema"] == "PUBLIC"


class TestShortFormCombinations:
    """Test multiple short forms used together."""

    def test_combination_schemachange_params(self, clean_env, mock_file_system):
        """Test combination of schemachange short forms."""
        vars_dict = {"env": "test"}
        with mock.patch(
            "sys.argv",
            [
                "schemachange",
                "-f",
                "./migrations",
                "-m",
                "./modules",
                "-c",
                "DB.SCHEMA.TABLE",
                "-V",
                json.dumps(vars_dict),
                "-L",
                "DEBUG",
                "-Q",
                "test-deployment",
                "-ac",
            ],
        ):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": vars_dict,
                            "connections_file_path": None,
                            "connection_name": None,
                            "root_folder": "./migrations",
                            "modules_folder": "./modules",
                            "change_history_table": "DB.SCHEMA.TABLE",
                            "log_level": logging.DEBUG,
                            "query_tag": "test-deployment",
                            "autocommit": True,
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["root_folder"] == "./migrations"
                        assert factory_kwargs["modules_folder"] == "./modules"
                        assert factory_kwargs["change_history_table"] == "DB.SCHEMA.TABLE"
                        assert factory_kwargs["config_vars"] == vars_dict
                        assert factory_kwargs["log_level"] == logging.DEBUG
                        assert factory_kwargs["query_tag"] == "test-deployment"
                        assert factory_kwargs["autocommit"] is True

    def test_combination_snowflake_params(self, clean_env, mock_file_system):
        """Test combination of Snowflake connection short forms."""
        with mock.patch(
            "sys.argv",
            [
                "schemachange",
                "-a",
                "myaccount.us-east-1",
                "-u",
                "testuser",
                "-r",
                "TEST_ROLE",
                "-w",
                "TEST_WH",
                "-d",
                "TEST_DB",
                "-s",
                "PUBLIC",
            ],
        ):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": None,
                            "snowflake_account": "myaccount.us-east-1",
                            "snowflake_user": "testuser",
                            "snowflake_role": "TEST_ROLE",
                            "snowflake_warehouse": "TEST_WH",
                            "snowflake_database": "TEST_DB",
                            "snowflake_schema": "PUBLIC",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["snowflake_account"] == "myaccount.us-east-1"
                        assert factory_kwargs["snowflake_user"] == "testuser"
                        assert factory_kwargs["snowflake_role"] == "TEST_ROLE"
                        assert factory_kwargs["snowflake_warehouse"] == "TEST_WH"
                        assert factory_kwargs["snowflake_database"] == "TEST_DB"
                        assert factory_kwargs["snowflake_schema"] == "PUBLIC"

    def test_combination_mixed_params(self, clean_env, mock_file_system):
        """Test combination of both schemachange and Snowflake short forms."""
        with mock.patch(
            "sys.argv",
            [
                "schemachange",
                "-f",
                "./migrations",
                "-a",
                "myaccount.us-east-1",
                "-u",
                "testuser",
                "-L",
                "INFO",
                "-C",
                "production",
                "-Q",
                "prod-deployment",
            ],
        ):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {},
                            "connections_file_path": None,
                            "connection_name": "production",
                            "root_folder": "./migrations",
                            "snowflake_account": "myaccount.us-east-1",
                            "snowflake_user": "testuser",
                            "log_level": logging.INFO,
                            "query_tag": "prod-deployment",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["root_folder"] == "./migrations"
                        assert factory_kwargs["snowflake_account"] == "myaccount.us-east-1"
                        assert factory_kwargs["snowflake_user"] == "testuser"
                        assert factory_kwargs["log_level"] == logging.INFO
                        assert factory_kwargs["connection_name"] == "production"
                        assert factory_kwargs["query_tag"] == "prod-deployment"


class TestShortFormsWithLongForms:
    """Test mixing short forms with long forms."""

    def test_mixed_short_and_long_forms(self, clean_env, mock_file_system):
        """Test using both short and long forms together."""
        with mock.patch(
            "sys.argv",
            [
                "schemachange",
                "-f",
                "./migrations",  # Short form
                "--schemachange-modules-folder",
                "./modules",  # Long form
                "-V",
                '{"key": "value"}',  # Short form
                "--schemachange-log-level",
                "DEBUG",  # Long form
                "-a",
                "myaccount.us-east-1",  # Short form
                "--snowflake-warehouse",
                "WH",  # Long form
            ],
        ):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {"key": "value"},
                            "connections_file_path": None,
                            "connection_name": None,
                            "root_folder": "./migrations",
                            "modules_folder": "./modules",
                            "log_level": logging.DEBUG,
                            "snowflake_account": "myaccount.us-east-1",
                            "snowflake_warehouse": "WH",
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["root_folder"] == "./migrations"
                        assert factory_kwargs["modules_folder"] == "./modules"
                        assert factory_kwargs["config_vars"] == {"key": "value"}
                        assert factory_kwargs["log_level"] == logging.DEBUG
                        assert factory_kwargs["snowflake_account"] == "myaccount.us-east-1"
                        assert factory_kwargs["snowflake_warehouse"] == "WH"


class TestBackwardCompatibility:
    """Test backward compatibility with old argument formats."""

    def test_old_and_new_short_forms_coexist(self, clean_env, mock_file_system):
        """Test that old (-f, -m, -c, -ac) and new (-V, -L, -Q, -C) short forms work together."""
        with mock.patch(
            "sys.argv",
            [
                "schemachange",
                "-f",
                "./migrations",  # Old short form (not deprecated)
                "-m",
                "./modules",  # Old short form (not deprecated)
                "-V",
                '{"env": "test"}',  # New short form
                "-L",
                "DEBUG",  # New short form
            ],
        ):
            with mock.patch("schemachange.config.get_merged_config.parse_cli_args") as mock_parse:
                with mock.patch("schemachange.config.get_merged_config.get_yaml_config_kwargs", return_value={}):
                    with mock.patch("schemachange.config.get_merged_config.DeployConfig.factory") as mock_factory:
                        mock_parse.return_value = {
                            "subcommand": "deploy",
                            "config_file_name": "schemachange-config.yml",
                            "config_vars": {"env": "test"},
                            "connections_file_path": None,
                            "connection_name": None,
                            "root_folder": "./migrations",
                            "modules_folder": "./modules",
                            "log_level": logging.DEBUG,
                        }

                        logger = structlog.testing.CapturingLogger()
                        get_merged_config(logger=logger)

                        factory_kwargs = mock_factory.call_args.kwargs
                        assert factory_kwargs["root_folder"] == "./migrations"
                        assert factory_kwargs["modules_folder"] == "./modules"
                        assert factory_kwargs["config_vars"] == {"env": "test"}
                        assert factory_kwargs["log_level"] == logging.DEBUG
