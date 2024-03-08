from __future__ import annotations

import os
from typing import Optional

import jinja2.ext


class JinjaEnvVar(jinja2.ext.Extension):
    """
    Extends Jinja Templates with access to environmental variables
    """

    def __init__(self, environment: jinja2.Environment):
        super().__init__(environment)

        # add globals
        environment.globals["env_var"] = JinjaEnvVar.env_var

    @staticmethod
    def env_var(env_var: str, default: Optional[str] = None) -> str:
        """
        Returns the value of the environmental variable or the default.
        """
        result = default
        if env_var in os.environ:
            result = os.environ[env_var]

        if result is None:
            raise ValueError(
                f"Could not find environmental variable {env_var} and no default value was provided"
            )

        return result
