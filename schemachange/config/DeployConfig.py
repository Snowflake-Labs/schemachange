from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Literal

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import (
    get_snowflake_identifier_string,
    get_snowflake_password,
)

@dataclasses.dataclass(frozen=True)
class DeployConfig(BaseConfig):
    subcommand: Literal["deploy"] = "deploy"
    snowflake_account: str | None = (
        None  # TODO: Remove when connections.toml is enforced
    )
    snowflake_user: str | None = None  # TODO: Remove when connections.toml is enforced
    snowflake_role: str | None = None  # TODO: Remove when connections.toml is enforced
    snowflake_warehouse: str | None = (
        None  # TODO: Remove when connections.toml is enforced
    )
    snowflake_database: str | None = (
        None  # TODO: Remove when connections.toml is enforced
    )
    snowflake_schema: str | None = (
        None  # TODO: Remove when connections.toml is enforced
    )
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

        # TODO: Remove when connections.toml is enforced
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

        change_history_table = ChangeHistoryTable.from_str(
            table_str=change_history_table
        )

        return super().factory(
            subcommand="deploy",
            config_file_path=config_file_path,
            change_history_table=change_history_table,
            **kwargs,
        )

    def get_session_kwargs(self) -> dict:
        session_kwargs = {
            "account": self.snowflake_account,  # TODO: Remove when connections.toml is enforced
            "user": self.snowflake_user,  # TODO: Remove when connections.toml is enforced
            "role": self.snowflake_role,  # TODO: Remove when connections.toml is enforced
            "warehouse": self.snowflake_warehouse,  # TODO: Remove when connections.toml is enforced
            "database": self.snowflake_database,  # TODO: Remove when connections.toml is enforced
            "schema": self.snowflake_schema,  # TODO: Remove when connections.toml is enforced
            "connections_file_path": self.connections_file_path,
            "connection_name": self.connection_name,
            "change_history_table": self.change_history_table,
            "autocommit": self.autocommit,
            "query_tag": self.query_tag
        }
        
        # TODO: Discuss the need for check for snowflake password before passing the session 
        # kwargs to open a snowflake session
        # snowflake_password = get_snowflake_password()
        # if snowflake_password is not None and snowflake_password:
        #    session_kwargs["password"] = snowflake_password 
        return {k: v for k, v in session_kwargs.items() if v is not None}
