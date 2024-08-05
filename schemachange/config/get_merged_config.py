import sys
from argparse import Namespace
from pathlib import Path
from typing import Union, Optional

from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.DeployConfig import DeployConfig
from schemachange.config.RenderConfig import RenderConfig
from schemachange.config.parse_cli_args import parse_cli_args
from schemachange.config.utils import load_yaml_config


def config_factory(args: Union[Namespace, dict]) -> Union[DeployConfig, RenderConfig]:
    if isinstance(args, Namespace):
        subcommand = args.subcommand
        kwargs = args.__dict__
    else:
        subcommand = args.get("subcommand")
        kwargs = args

    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    if "change_history_table" in kwargs and kwargs["change_history_table"] is not None:
        kwargs["change_history_table"] = ChangeHistoryTable.from_str(
            table_str=kwargs["change_history_table"]
        )

    if "vars" in kwargs:
        kwargs["config_vars"] = kwargs.pop("vars")

    if subcommand == "deploy":
        return DeployConfig.factory(**kwargs)
    elif subcommand == "render":
        return RenderConfig.factory(**kwargs)
    else:
        raise Exception(f"unhandled subcommand: {subcommand}")


def get_yaml_config(
    subcommand: str,
    config_file_path: Optional[Path],
    script_path: Optional[Path] = None,
) -> Union[DeployConfig, RenderConfig]:
    # TODO: I think the configuration key for oauthconfig should be oauth-config.
    #  This looks like a bug in the current state of the repo to me

    # load YAML inputs and convert kebabs to snakes
    kwargs = {
        k.replace("-", "_").replace("oauthconfig", "oauth_config"): v
        for (k, v) in load_yaml_config(config_file_path).items()
    }
    kwargs["subcommand"] = subcommand
    if script_path:
        kwargs["script_path"] = script_path

    if "verbose" in kwargs:
        kwargs["log_level"] = "DEBUG" if kwargs["verbose"] else "ERROR"
        kwargs.pop("verbose")

    return config_factory(kwargs)


def get_merged_config() -> Union[DeployConfig, RenderConfig]:
    args = parse_cli_args(sys.argv[1:])
    cli_config = config_factory(args=args)
    yaml_config = get_yaml_config(
        subcommand=cli_config.subcommand,
        config_file_path=cli_config.config_file_path,
        script_path=getattr(cli_config, "script_path", None),
    )

    # override the YAML config with the CLI configuration
    return yaml_config.merge_exclude_defaults(other=cli_config)
