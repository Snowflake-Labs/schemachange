"""
Unit tests for the parameter_mapping module.
"""

from schemachange.config.parameter_mapping import (
    ALL_PARAMETERS,
    CLI_LONG_TO_PARAM,
    CLI_SHORT_TO_PARAM,
    DEPRECATED_CLI_TO_PARAM,
    ENV_VAR_TO_PARAM,
    PYTHON_NAME_TO_PARAM,
    SCHEMACHANGE_PARAMETERS,
    SNOWFLAKE_AUTH_PARAMETERS,
    SNOWFLAKE_CONNECTION_PARAMETERS,
    SNOWFLAKE_CONNECTOR_BOOLEAN_PARAMS,
    SNOWFLAKE_CONNECTOR_NUMERIC_PARAMS,
    YAML_KEY_TO_PARAM,
    Parameter,
    ParameterCategory,
    ParameterType,
    convert_kebab_to_snake,
    convert_snake_to_kebab,
    convert_snake_to_upper_snake,
    get_new_cli_arg_for_deprecated,
    get_parameter_by_cli_arg,
    get_parameter_by_env_var,
    get_parameter_by_python_name,
    get_parameter_by_yaml_key,
    get_parameters_by_category,
    get_schemachange_env_var_names,
    get_snowflake_env_var_names,
    is_deprecated_cli_arg,
)


class TestParameterClass:
    """Tests for the Parameter class."""

    def test_parameter_initialization(self):
        """Test that Parameter objects are initialized correctly."""
        param = Parameter(
            python_name="test_param",
            cli_long="--schemachange-test-param",
            cli_short="-t",
            env_var="SCHEMACHANGE_TEST_PARAM",
            param_type=ParameterType.STRING,
            category=ParameterCategory.SCHEMACHANGE,
            deprecated_cli_names=["--test-param"],
            description="Test parameter",
            default="test_default",
        )

        assert param.python_name == "test_param"
        assert param.cli_long == "--schemachange-test-param"
        assert param.cli_short == "-t"
        assert param.env_var == "SCHEMACHANGE_TEST_PARAM"
        assert param.param_type == ParameterType.STRING
        assert param.category == ParameterCategory.SCHEMACHANGE
        assert param.deprecated_cli_names == ["--test-param"]
        assert param.description == "Test parameter"
        assert param.default == "test_default"

    def test_parameter_yaml_key_schemachange(self):
        """Test that YAML keys are correctly derived for schemachange parameters."""
        param = Parameter(
            python_name="root_folder",
            cli_long="--schemachange-root-folder",
            env_var="SCHEMACHANGE_ROOT_FOLDER",
            param_type=ParameterType.PATH,
            category=ParameterCategory.SCHEMACHANGE,
        )

        assert param.yaml_key == "root-folder"

    def test_parameter_yaml_key_snowflake(self):
        """Test that YAML keys are correctly derived for snowflake parameters."""
        param = Parameter(
            python_name="snowflake_account",
            cli_long="--snowflake-account",
            env_var="SNOWFLAKE_ACCOUNT",
            param_type=ParameterType.STRING,
            category=ParameterCategory.SNOWFLAKE_CONNECTION,
        )

        assert param.yaml_key == "account"


class TestParameterLookups:
    """Tests for parameter lookup dictionaries."""

    def test_all_parameters_has_all_categories(self):
        """Test that ALL_PARAMETERS contains parameters from all categories."""
        categories = {param.category for param in ALL_PARAMETERS}

        assert ParameterCategory.SCHEMACHANGE in categories
        assert ParameterCategory.SNOWFLAKE_CONNECTION in categories
        assert ParameterCategory.SNOWFLAKE_AUTH in categories

    def test_python_name_lookup(self):
        """Test that Python name lookup works correctly."""
        param = PYTHON_NAME_TO_PARAM.get("root_folder")

        assert param is not None
        assert param.python_name == "root_folder"
        assert param.cli_long == "--schemachange-root-folder"
        assert param.env_var == "SCHEMACHANGE_ROOT_FOLDER"

    def test_cli_long_lookup(self):
        """Test that CLI long form lookup works correctly."""
        param = CLI_LONG_TO_PARAM.get("--schemachange-root-folder")

        assert param is not None
        assert param.python_name == "root_folder"

    def test_cli_short_lookup(self):
        """Test that CLI short form lookup works correctly."""
        param = CLI_SHORT_TO_PARAM.get("-f")

        assert param is not None
        assert param.python_name == "root_folder"
        assert param.cli_short == "-f"

    def test_env_var_lookup(self):
        """Test that environment variable lookup works correctly."""
        param = ENV_VAR_TO_PARAM.get("SCHEMACHANGE_ROOT_FOLDER")

        assert param is not None
        assert param.python_name == "root_folder"

    def test_deprecated_cli_lookup(self):
        """Test that deprecated CLI argument lookup works correctly."""
        param = DEPRECATED_CLI_TO_PARAM.get("--vars")

        assert param is not None
        assert param.python_name == "config_vars"
        assert param.cli_long == "--schemachange-vars"

    def test_yaml_key_lookup(self):
        """Test that YAML key lookup works correctly."""
        param = YAML_KEY_TO_PARAM.get("root-folder")

        assert param is not None
        assert param.python_name == "root_folder"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_parameter_by_python_name(self):
        """Test getting parameter by Python name."""
        param = get_parameter_by_python_name("root_folder")

        assert param is not None
        assert param.python_name == "root_folder"

    def test_get_parameter_by_python_name_not_found(self):
        """Test getting parameter by non-existent Python name."""
        param = get_parameter_by_python_name("non_existent_param")

        assert param is None

    def test_get_parameter_by_cli_arg_long_form(self):
        """Test getting parameter by CLI long form."""
        param = get_parameter_by_cli_arg("--schemachange-root-folder")

        assert param is not None
        assert param.python_name == "root_folder"

    def test_get_parameter_by_cli_arg_short_form(self):
        """Test getting parameter by CLI short form."""
        param = get_parameter_by_cli_arg("-f")

        assert param is not None
        assert param.python_name == "root_folder"

    def test_get_parameter_by_cli_arg_deprecated(self):
        """Test getting parameter by deprecated CLI argument."""
        param = get_parameter_by_cli_arg("--vars")

        assert param is not None
        assert param.python_name == "config_vars"

    def test_get_parameter_by_env_var(self):
        """Test getting parameter by environment variable name."""
        param = get_parameter_by_env_var("SCHEMACHANGE_ROOT_FOLDER")

        assert param is not None
        assert param.python_name == "root_folder"

    def test_get_parameter_by_yaml_key(self):
        """Test getting parameter by YAML key."""
        param = get_parameter_by_yaml_key("root-folder")

        assert param is not None
        assert param.python_name == "root_folder"

    def test_is_deprecated_cli_arg_true(self):
        """Test deprecated CLI argument detection."""
        assert is_deprecated_cli_arg("--vars") is True
        assert is_deprecated_cli_arg("--query-tag") is True
        assert is_deprecated_cli_arg("--log-level") is True

    def test_is_deprecated_cli_arg_false(self):
        """Test non-deprecated CLI argument detection."""
        assert is_deprecated_cli_arg("--schemachange-vars") is False
        assert is_deprecated_cli_arg("-V") is False

    def test_get_new_cli_arg_for_deprecated(self):
        """Test getting new CLI argument for deprecated one."""
        long_form, short_form = get_new_cli_arg_for_deprecated("--vars")

        assert long_form == "--schemachange-vars"
        assert short_form == "-V"

    def test_get_new_cli_arg_for_deprecated_no_short(self):
        """Test getting new CLI argument for deprecated one without short form."""
        long_form, short_form = get_new_cli_arg_for_deprecated("--dry-run")

        assert long_form == "--schemachange-dry-run"
        assert short_form is None

    def test_convert_kebab_to_snake(self):
        """Test kebab-case to snake_case conversion."""
        assert convert_kebab_to_snake("root-folder") == "root_folder"
        assert convert_kebab_to_snake("change-history-table") == "change_history_table"

    def test_convert_snake_to_kebab(self):
        """Test snake_case to kebab-case conversion."""
        assert convert_snake_to_kebab("root_folder") == "root-folder"
        assert convert_snake_to_kebab("change_history_table") == "change-history-table"

    def test_convert_snake_to_upper_snake(self):
        """Test snake_case to UPPER_SNAKE_CASE conversion."""
        assert convert_snake_to_upper_snake("root_folder") == "ROOT_FOLDER"
        assert convert_snake_to_upper_snake("change_history_table") == "CHANGE_HISTORY_TABLE"

    def test_get_parameters_by_category_schemachange(self):
        """Test getting parameters by schemachange category."""
        params = get_parameters_by_category(ParameterCategory.SCHEMACHANGE)

        assert len(params) > 0
        assert all(p.category == ParameterCategory.SCHEMACHANGE for p in params)

        # Verify specific parameters are included
        param_names = {p.python_name for p in params}
        assert "root_folder" in param_names
        assert "modules_folder" in param_names
        assert "config_vars" in param_names

    def test_get_parameters_by_category_snowflake(self):
        """Test getting parameters by snowflake connection category."""
        params = get_parameters_by_category(ParameterCategory.SNOWFLAKE_CONNECTION)

        assert len(params) > 0
        assert all(p.category == ParameterCategory.SNOWFLAKE_CONNECTION for p in params)

        # Verify specific parameters are included
        param_names = {p.python_name for p in params}
        assert "snowflake_account" in param_names
        assert "snowflake_user" in param_names
        assert "snowflake_role" in param_names

    def test_get_schemachange_env_var_names(self):
        """Test getting all SCHEMACHANGE_* environment variable names."""
        env_vars = get_schemachange_env_var_names()

        assert len(env_vars) > 0
        assert all(ev.startswith("SCHEMACHANGE_") for ev in env_vars)
        assert "SCHEMACHANGE_ROOT_FOLDER" in env_vars
        assert "SCHEMACHANGE_VARS" in env_vars

    def test_get_snowflake_env_var_names(self):
        """Test getting all SNOWFLAKE_* environment variable names."""
        env_vars = get_snowflake_env_var_names()

        assert len(env_vars) > 0
        assert all(ev.startswith("SNOWFLAKE_") for ev in env_vars)
        assert "SNOWFLAKE_ACCOUNT" in env_vars
        assert "SNOWFLAKE_USER" in env_vars
        assert "SNOWFLAKE_AUTHENTICATOR" in env_vars


class TestNewShortForms:
    """Test that new short forms are correctly mapped."""

    def test_new_capital_short_forms_exist(self):
        """Test that new capital letter short forms exist."""
        # New short forms introduced
        assert CLI_SHORT_TO_PARAM.get("-V") is not None  # vars
        assert CLI_SHORT_TO_PARAM.get("-L") is not None  # log-level
        assert CLI_SHORT_TO_PARAM.get("-Q") is not None  # query-tag
        assert CLI_SHORT_TO_PARAM.get("-C") is not None  # connection-name

    def test_new_capital_short_forms_map_correctly(self):
        """Test that new capital short forms map to correct parameters."""
        assert CLI_SHORT_TO_PARAM["-V"].python_name == "config_vars"
        assert CLI_SHORT_TO_PARAM["-L"].python_name == "log_level"
        assert CLI_SHORT_TO_PARAM["-Q"].python_name == "query_tag"
        assert CLI_SHORT_TO_PARAM["-C"].python_name == "connection_name"

    def test_existing_lowercase_short_forms_exist(self):
        """Test that existing lowercase short forms still exist."""
        assert CLI_SHORT_TO_PARAM.get("-f") is not None  # root-folder
        assert CLI_SHORT_TO_PARAM.get("-m") is not None  # modules-folder
        assert CLI_SHORT_TO_PARAM.get("-c") is not None  # change-history-table
        assert CLI_SHORT_TO_PARAM.get("-ac") is not None  # autocommit


class TestSnowflakeConnectorParameters:
    """Test Snowflake connector parameter definitions."""

    def test_boolean_params_defined(self):
        """Test that boolean connector parameters are defined."""
        assert "client_session_keep_alive" in SNOWFLAKE_CONNECTOR_BOOLEAN_PARAMS
        assert "validate_default_parameters" in SNOWFLAKE_CONNECTOR_BOOLEAN_PARAMS

    def test_numeric_params_defined(self):
        """Test that numeric connector parameters are defined."""
        assert "login_timeout" in SNOWFLAKE_CONNECTOR_NUMERIC_PARAMS
        assert "network_timeout" in SNOWFLAKE_CONNECTOR_NUMERIC_PARAMS
        assert "client_prefetch_threads" in SNOWFLAKE_CONNECTOR_NUMERIC_PARAMS


class TestParameterConsistency:
    """Test consistency across parameter definitions."""

    def test_no_duplicate_python_names(self):
        """Test that there are no duplicate Python parameter names."""
        python_names = [param.python_name for param in ALL_PARAMETERS]
        assert len(python_names) == len(set(python_names))

    def test_no_duplicate_cli_long_forms(self):
        """Test that there are no duplicate CLI long forms."""
        cli_longs = [param.cli_long for param in ALL_PARAMETERS]
        assert len(cli_longs) == len(set(cli_longs))

    def test_no_duplicate_cli_short_forms(self):
        """Test that there are no duplicate CLI short forms."""
        cli_shorts = [param.cli_short for param in ALL_PARAMETERS if param.cli_short]
        assert len(cli_shorts) == len(set(cli_shorts))

    def test_no_duplicate_env_vars(self):
        """Test that there are no duplicate environment variable names."""
        env_vars = [param.env_var for param in ALL_PARAMETERS]
        assert len(env_vars) == len(set(env_vars))

    def test_schemachange_params_have_correct_prefix(self):
        """Test that schemachange parameters have correct CLI and ENV prefixes."""
        for param in SCHEMACHANGE_PARAMETERS:
            assert param.cli_long.startswith("--schemachange-")
            assert param.env_var.startswith("SCHEMACHANGE_")

    def test_snowflake_params_have_correct_prefix(self):
        """Test that snowflake parameters have correct CLI and ENV prefixes."""
        for param in SNOWFLAKE_CONNECTION_PARAMETERS + SNOWFLAKE_AUTH_PARAMETERS:
            assert param.cli_long.startswith("--snowflake-")
            assert param.env_var.startswith("SNOWFLAKE_")


class TestDeprecatedMappings:
    """Test deprecated CLI argument mappings."""

    def test_all_deprecated_args_map_to_new_params(self):
        """Test that all deprecated CLI arguments map to valid parameters."""
        for deprecated_arg, param in DEPRECATED_CLI_TO_PARAM.items():
            assert deprecated_arg.startswith("--")
            assert param is not None
            assert param in ALL_PARAMETERS

    def test_vars_deprecation(self):
        """Test --vars deprecation mapping."""
        param = DEPRECATED_CLI_TO_PARAM.get("--vars")
        assert param.cli_long == "--schemachange-vars"
        assert param.cli_short == "-V"

    def test_query_tag_deprecation(self):
        """Test --query-tag deprecation mapping."""
        param = DEPRECATED_CLI_TO_PARAM.get("--query-tag")
        assert param.cli_long == "--schemachange-query-tag"
        assert param.cli_short == "-Q"

    def test_log_level_deprecation(self):
        """Test --log-level deprecation mapping."""
        param = DEPRECATED_CLI_TO_PARAM.get("--log-level")
        assert param.cli_long == "--schemachange-log-level"
        assert param.cli_short == "-L"
