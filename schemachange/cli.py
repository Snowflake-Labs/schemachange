import hashlib
from pathlib import Path

import structlog
from structlog import BoundLogger

from schemachange.JinjaTemplateProcessor import JinjaTemplateProcessor
from schemachange.config.RenderConfig import RenderConfig
from schemachange.config.get_merged_config import get_merged_config
from schemachange.deploy import deploy
from schemachange.redact_config_secrets import redact_config_secrets
from schemachange.session.SnowflakeSession import get_session_from_config

# region Global Variables
# metadata
SCHEMACHANGE_VERSION = "4.0.0"
SNOWFLAKE_APPLICATION_NAME = "schemachange"
module_logger = structlog.getLogger(__name__)


def render(config: RenderConfig, script_path: Path, logger: BoundLogger) -> None:
    """
    Renders the provided script.

    Note: does not apply secrets filtering.
    """
    # Always process with jinja engine
    jinja_processor = JinjaTemplateProcessor(
        project_root=config.root_folder, modules_folder=config.modules_folder
    )
    content = jinja_processor.render(
        jinja_processor.relpath(script_path), config.config_vars
    )

    checksum = hashlib.sha224(content.encode("utf-8")).hexdigest()
    logger.info("Success", checksum=checksum, content=content)


def main():
    module_logger.info(
        "schemachange version: %(schemachange_version)s"
        % {"schemachange_version": SCHEMACHANGE_VERSION}
    )

    config = get_merged_config()
    redact_config_secrets(config_secrets=config.secrets)

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(config.log_level),
    )

    logger = structlog.getLogger()
    logger = logger.bind(schemachange_version=SCHEMACHANGE_VERSION)

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
