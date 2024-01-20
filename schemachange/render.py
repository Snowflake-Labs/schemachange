import hashlib
from pathlib import Path

import structlog

from schemachange.Config import RenderConfig
from schemachange.JinjaTemplateProcessor import JinjaTemplateProcessor


logger = structlog.getLogger(__name__)


def render(config: RenderConfig, script_path: Path) -> None:
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
