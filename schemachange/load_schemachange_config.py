from __future__ import annotations

from pathlib import Path

import jinja2
import jinja2.ext
import yaml

from schemachange.JinjaEnvVar import JinjaEnvVar


def load_schemachange_config(config_file_path: Path) -> dict[str, object]:
    """
    Loads the schemachange config file and processes with jinja templating engine
    """
    config = dict()

    # First read in the yaml config file, if present
    if config_file_path.is_file():
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
        print(f"Using config file: {str(config_file_path)}")
    return config
