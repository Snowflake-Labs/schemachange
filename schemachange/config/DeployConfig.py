from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Literal

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import get_snowflake_identifier_string


@dataclasses.dataclass(frozen=True)
class DeployConfig(BaseConfig):
    subcommand: Literal["deploy"] = "deploy"
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_role: str | None = None
    snowflake_warehouse: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str | None = None
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
        snowflake_role: str | None = None,
        snowflake_warehouse: str | None = None,
        snowflake_database: str | None = None,
        snowflake_schema: str | None = None,
        change_history_table: str | None = None,
        **kwargs,
    ):
        if "subcommand" in kwargs:
            kwargs.pop("subcommand")

        change_history_table = ChangeHistoryTable.from_str(
            table_str=change_history_table
        )

        return super().factory(
            subcommand="deploy",
            config_file_path=config_file_path,
            snowflake_role=get_snowflake_identifier_string(
                snowflake_role, "snowflake_role"
            ),
            snowflake_warehouse=get_snowflake_identifier_string(
                snowflake_warehouse, "snowflake_warehouse"
            ),
            snowflake_database=get_snowflake_identifier_string(
                snowflake_database, "snowflake_database"
            ),
            snowflake_schema=get_snowflake_identifier_string(
                snowflake_schema, "snowflake_schema"
            ),
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
        missing_args = [key for key, value in req_args.items() if value is None]

        if len(missing_args) == 0:
            return

        missing_args = ", ".join({arg.replace("_", " ") for arg in missing_args})
        raise ValueError(
            f"Missing config values. The following config values are required: {missing_args}"
        )
