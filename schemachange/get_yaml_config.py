from __future__ import annotations


import jinja2
import jinja2.ext
import structlog
import yaml

from schemachange.JinjaEnvVar import JinjaEnvVar

from pathlib import Path

from Config import DeployConfig, RenderConfig, config_factory


logger = structlog.getLogger(__name__)


def load_yaml_config(config_file_path: Path | None) -> dict[str, object]:
    """
    Loads the schemachange config file and processes with jinja templating engine
    """
    config = dict()

    # First read in the yaml config file, if present
    if config_file_path is not None and config_file_path.is_file():
        with config_file_path.open() as config_file:
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
        logger.info("Using config file", config_file_path=str(config_file_path))
    return config


def get_yaml_config(
    subcommand: str, config_file_path: Path | None, script_path: Path | None = None
) -> DeployConfig | RenderConfig:
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

    return config_factory(kwargs)
