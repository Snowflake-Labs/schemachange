from __future__ import annotations

import sys

import structlog
import hashlib
from pathlib import Path

from structlog import BoundLogger

from schemachange.redact_config_secrets import redact_config_secrets
from schemachange.deploy import deploy
from schemachange.Config import config_factory, DeployConfig, RenderConfig
from schemachange.get_yaml_config import get_yaml_config
from schemachange.parse_cli_args import parse_cli_args
from schemachange.session.SnowflakeSession import get_session_from_config
from schemachange.JinjaTemplateProcessor import JinjaTemplateProcessor


SCHEMACHANGE_VERSION = "3.6.1"
SNOWFLAKE_APPLICATION_NAME = "schemachange"
module_logger = structlog.getLogger(__name__)


def get_merged_config() -> DeployConfig | RenderConfig:
    args = parse_cli_args(sys.argv[1:])
    cli_config = config_factory(args=args)
    yaml_config = get_yaml_config(
        subcommand=cli_config.subcommand,
        config_file_path=cli_config.config_file_path,
        script_path=getattr(cli_config, "script_path", None),
    )

    # override the YAML config with the CLI configuration
    return yaml_config.merge_exclude_unset(other=cli_config)


def render(config: RenderConfig, script_path: Path, logger: BoundLogger) -> None:
    """
    Renders the provided script.

    Note: does not apply secrets filtering.
    """
    # Always process with jinja engine
    jinja_processor = JinjaTemplateProcessor(
        project_root=config.root_folder, modules_folder=config.modules_folder
    )
    content = jinja_processor.render(jinja_processor.relpath(script_path), config.vars)

    checksum = hashlib.sha224(content.encode("utf-8")).hexdigest()
    logger.log("Success", checksum=checksum, content=content)


def main():
    module_logger.info(
        "schemachange version: %(schemachange_version)s"
        % {"schemachange_version": SCHEMACHANGE_VERSION}
    )
    logger = module_logger.bind(schemachange_version=SCHEMACHANGE_VERSION)

    config = get_merged_config()
    redact_config_secrets(config_secrets=config.secrets)

    config.log_details()

    # Finally, execute the command
    if config.subcommand == "render":
        render(
            config=config,
            script_path=config.script_path,
            logger=logger,
        )
    else:
        config.check_for_deploy_args()
        session = get_session_from_config(
            config=config,
            schemachange_version=SCHEMACHANGE_VERSION,
            snowflake_application_name=SNOWFLAKE_APPLICATION_NAME,
            logger=logger,
        )
        deploy(config=config, session=session)


if __name__ == "__main__":
    main()
