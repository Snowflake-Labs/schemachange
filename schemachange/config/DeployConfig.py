from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Literal

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import (
    get_snowflake_identifier_string,
    validate_file_path,
    get_oauth_token,
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class DeployConfig(BaseConfig):
    subcommand: Literal["deploy"] = "deploy"
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_role: str | None = None
    snowflake_warehouse: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str | None = None
    snowflake_authenticator: str | None = "snowflake"
    snowflake_password: str | None = None
    snowflake_oauth_token: str | None = None
    snowflake_private_key_path: Path | None = None
    connections_file_path: Path | None = None
    connection_name: str | None = None
    # TODO: Turn change_history_table into three arguments. There's no need to parse it from a string
    change_history_table: ChangeHistoryTable | None = dataclasses.field(
        default_factory=ChangeHistoryTable
    )
    create_change_history_table: bool = False
    autocommit: bool = False
    dry_run: bool = False
    query_tag: str | None = None

    @classmethod
    def factory(
        cls,
        config_file_path: Path,
        change_history_table: str | None = None,
        **kwargs,
    ):
        if "subcommand" in kwargs:
            kwargs.pop("subcommand")

        for sf_input in [
            "snowflake_role",
            "snowflake_warehouse",
            "snowflake_database",
            "snowflake_schema",
        ]:
            if sf_input in kwargs and kwargs[sf_input] is not None:
                kwargs[sf_input] = get_snowflake_identifier_string(
                    kwargs[sf_input], sf_input
                )

        for sf_path_input in [
            "snowflake_private_key_path",
            "snowflake_token_path",
        ]:
            if sf_path_input in kwargs and kwargs[sf_path_input] is not None:
                kwargs[sf_path_input] = validate_file_path(
                    file_path=kwargs[sf_path_input]
                )

        # If set by an environment variable, pop snowflake_token_path from kwargs
        if "snowflake_oauth_token" in kwargs:
            kwargs.pop("snowflake_token_path", None)
            kwargs.pop("oauth_config", None)
        # Load it from a file, if provided
        elif "snowflake_token_path" in kwargs:
            kwargs.pop("oauth_config", None)
            oauth_token_path = kwargs.pop("snowflake_token_path")
            with open(oauth_token_path) as f:
                kwargs["snowflake_oauth_token"] = f.read()
        # Make the oauth call if authenticator == "oauth"

        elif "oauth_config" in kwargs:
            oauth_config = kwargs.pop("oauth_config")
            authenticator = kwargs.get("snowflake_authenticator")
            if authenticator is not None and authenticator.lower() == "oauth":
                kwargs["snowflake_oauth_token"] = get_oauth_token(oauth_config)

        change_history_table = ChangeHistoryTable.from_str(
            table_str=change_history_table
        )

        return super().factory(
            subcommand="deploy",
            config_file_path=config_file_path,
            change_history_table=change_history_table,
            **kwargs,
        )

    def check_for_deploy_args(self) -> None:
        """Make sure we have the required connection info"""

        req_args = {
            "snowflake_account": self.snowflake_account,
            "snowflake_user": self.snowflake_user,
            "snowflake_role": self.snowflake_role,
            "snowflake_warehouse": self.snowflake_warehouse,
        }

        # OAuth based authentication
        if self.snowflake_authenticator.lower() == "oauth":
            req_args["snowflake_oauth_token"] = self.snowflake_oauth_token

        # External Browser based SSO
        elif self.snowflake_authenticator.lower() == "externalbrowser":
            pass

        # IDP based Authentication, limited to Okta
        elif self.snowflake_authenticator.lower()[:8] == "https://":
            req_args["snowflake_password"] = self.snowflake_password

        elif self.snowflake_authenticator.lower() == "snowflake_jwt":
            req_args["snowflake_private_key_path"] = self.snowflake_private_key_path

        elif self.snowflake_authenticator.lower() == "snowflake":
            req_args["snowflake_password"] = self.snowflake_password

        else:
            raise ValueError(
                f"{self.snowflake_authenticator} is not supported authenticator option. "
                "Choose from snowflake, snowflake_jwt, externalbrowser, oauth, https://<subdomain>.okta.com."
            )

        missing_args = [key for key, value in req_args.items() if value is None]

        if len(missing_args) == 0:
            return

        missing_args = ", ".join({arg.replace("_", " ") for arg in missing_args})
        raise ValueError(
            f"Missing config values. The following config values are required: {missing_args}"
        )

    def get_session_kwargs(self) -> dict:
        session_kwargs = {
            "account": self.snowflake_account,
            "user": self.snowflake_user,
            "role": self.snowflake_role,
            "warehouse": self.snowflake_warehouse,
            "database": self.snowflake_database,
            "schema": self.snowflake_schema,
            "authenticator": self.snowflake_authenticator,
            "password": self.snowflake_password,
            "oauth_token": self.snowflake_oauth_token,
            "private_key_path": self.snowflake_private_key_path,
            "connections_file_path": self.connections_file_path,
            "connection_name": self.connection_name,
            "change_history_table": self.change_history_table,
            "autocommit": self.autocommit,
            "query_tag": self.query_tag,
        }
        return {k: v for k, v in session_kwargs.items() if v is not None}
