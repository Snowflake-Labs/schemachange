from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import Literal

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import (
    get_snowflake_identifier_string,
    validate_file_path,
    set_connections_toml_path,
    get_connection_kwargs,
    get_snowflake_password,
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
    snowflake_authenticator: str | None = None
    snowflake_password: str | None = None
    snowflake_private_key_path: Path | None = None
    snowflake_token_path: Path | None = None
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
    oauth_config: dict | None = None

    @classmethod
    def factory(
        cls,
        config_file_path: Path,
        change_history_table: str | None = None,
        connections_file_path: str | None = None,
        connection_name: str | None = None,
        **kwargs,
    ):
        if "subcommand" in kwargs:
            kwargs.pop("subcommand")

        kwargs["snowflake_password"] = get_snowflake_password()
        if os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH") is not None:
            kwargs["snowflake_private_key_path"] = os.getenv(
                "SNOWFLAKE_PRIVATE_KEY_PATH"
            )

        if connections_file_path is not None:
            connections_file_path = validate_file_path(file_path=connections_file_path)
            set_connections_toml_path(connections_file_path=connections_file_path)

        if connection_name is not None:
            connection_kwargs = get_connection_kwargs(connection_name=connection_name)
            kwargs = {
                **connection_kwargs,
                **{k: v for k, v in kwargs.items() if v is not None},
            }

        for sf_input in [
            "snowflake_role",
            "snowflake_warehouse",
            "snowflake_database",
            "snowflake_schema",
        ]:
            if sf_input in kwargs:
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

        change_history_table = ChangeHistoryTable.from_str(
            table_str=change_history_table
        )

        return super().factory(
            subcommand="deploy",
            config_file_path=config_file_path,
            change_history_table=change_history_table,
            connections_file_path=connections_file_path,
            connection_name=connection_name,
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
        missing_args = [key for key, value in req_args.items() if value is None]

        if len(missing_args) == 0:
            return

        missing_args = ", ".join({arg.replace("_", " ") for arg in missing_args})
        raise ValueError(
            f"Missing config values. The following config values are required: {missing_args}"
        )
