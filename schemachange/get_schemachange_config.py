from __future__ import annotations

import os

import jinja2
import jinja2.ext
import yaml

from schemachange.JinjaEnvVar import JinjaEnvVar

CONFIG_DEFAULTS = {
    "root_folder": os.path.abspath("."),
    "modules_folder": None,
    "snowflake_account": None,
    "snowflake_user": None,
    "snowflake_role": None,
    "snowflake_warehouse": None,
    "snowflake_database": None,
    "snowflake_schema": None,
    "change_history_table": None,
    "vars": {},
    "create_change_history_table": False,
    "autocommit": False,
    "verbose": False,
    "dry_run": False,
    "query_tag": None,
    "oauth_config": None,
}


def load_schemachange_config(config_file_path: str) -> dict[str, object]:
    """
    Loads the schemachange config file and processes with jinja templating engine
    """
    config = dict()

    # First read in the yaml config file, if present
    if os.path.isfile(config_file_path):
        with open(config_file_path) as config_file:
            # Run the config file through the jinja engine to give access to environmental variables
            # The config file does not have the same access to the jinja functionality that a script
            # has.
            config_template = jinja2.Template(
                config_file.read(),
                undefined=jinja2.StrictUndefined,
                extensions=[JinjaEnvVar],
            )

            # The FullLoader parameter handles the conversion from YAML scalar values to Python the dictionary format
            config = yaml.load(config_template.render(), Loader=yaml.FullLoader)
        print("Using config file: %s" % config_file_path)
    return config


def get_schemachange_config(
    config_file_path,
    root_folder,
    modules_folder,
    snowflake_account,
    snowflake_user,
    snowflake_role,
    snowflake_warehouse,
    snowflake_database,
    snowflake_schema,
    change_history_table,
    vars,
    create_change_history_table,
    autocommit,
    verbose,
    dry_run,
    query_tag,
    oauth_config,
    **kwargs,
):
    # create cli override dictionary
    # Could refactor to just pass Args as a dictionary?
    # **kwargs inlcuded to avoid complaints about unexpect arguments from arg parser eg:subcommand
    cli_inputs = {
        "root_folder": root_folder,
        "modules_folder": modules_folder,
        "snowflake_account": snowflake_account,
        "snowflake_user": snowflake_user,
        "snowflake_role": snowflake_role,
        "snowflake_warehouse": snowflake_warehouse,
        "snowflake_database": snowflake_database,
        "snowflake_schema": snowflake_schema,
        "change_history_table": change_history_table,
        "vars": vars,
        "create_change_history_table": create_change_history_table,
        "autocommit": autocommit,
        "verbose": verbose,
        "dry_run": dry_run,
        "query_tag": query_tag,
        "oauth_config": oauth_config,
    }
    cli_inputs = {k: v for (k, v) in cli_inputs.items() if v}

    # load YAML inputs and convert kebabs to snakes
    config = {
        k.replace("-", "_"): v
        for (k, v) in load_schemachange_config(config_file_path).items()
    }
    # set values passed into the cli Overriding values in config file
    config.update(cli_inputs)

    # insert default values for items not populated
    config.update(
        {k: v for (k, v) in CONFIG_DEFAULTS.items() if k not in config.keys()}
    )

    # Validate folder paths
    if "root_folder" in config:
        config["root_folder"] = os.path.abspath(config["root_folder"])
    if not os.path.isdir(config["root_folder"]):
        raise ValueError(f"Invalid root folder: {config['root_folder']}")

    if config["modules_folder"]:
        config["modules_folder"] = os.path.abspath(config["modules_folder"])
        if not os.path.isdir(config["modules_folder"]):
            raise ValueError(f"Invalid modules folder: {config['modules_folder']}")
    if config["vars"]:
        # if vars is configured wrong in the config file it will come through as a string
        if type(config["vars"]) is not dict:
            raise ValueError(
                "vars did not parse correctly, please check its configuration"
            )

        # the variable schema change has been reserved
        if "schemachange" in config["vars"]:
            raise ValueError(
                "The variable schemachange has been reserved for use by schemachange, please use a different name"
            )

    return config
