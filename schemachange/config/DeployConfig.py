from __future__ import annotations

import dataclasses
from typing import Literal

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import get_snowflake_identifier_string


@dataclasses.dataclass(frozen=True, kw_only=True)
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
    _create_change_history_table: bool | None
    _autocommit: bool | None
    _dry_run: bool | None
    query_tag: str | None = None
    oauth_config: dict | None = None
    version_number_validation_regex: str | None = None
    _raise_exception_on_ignored_versioned_script: bool | None

    @property
    def create_change_history_table(self) -> bool:
        if self._create_change_history_table is None:
            return False
        return self._create_change_history_table

    @property
    def autocommit(self) -> bool:
        if self._autocommit is None:
            return False
        return self._autocommit

    @property
    def dry_run(self) -> bool:
        if self._dry_run is None:
            return False
        return self._dry_run

    @property
    def raise_exception_on_ignored_versioned_script(self) -> bool:
        if self._raise_exception_on_ignored_versioned_script is None:
            return False
        return self._raise_exception_on_ignored_versioned_script

    @classmethod
    def factory(
        cls,
        snowflake_role: str | None = None,
        snowflake_warehouse: str | None = None,
        snowflake_database: str | None = None,
        snowflake_schema: str | None = None,
        create_change_history_table: bool | None = None,
        autocommit: bool | None = None,
        dry_run: bool | None = None,
        raise_exception_on_ignored_versioned_script: bool | None = None,
        **kwargs,
    ):
        if "subcommand" in kwargs:
            kwargs.pop("subcommand")

        return super().factory(
            subcommand="deploy",
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
            _create_change_history_table=create_change_history_table,
            _autocommit=autocommit,
            _dry_run=dry_run,
            _raise_exception_on_ignored_versioned_script=raise_exception_on_ignored_versioned_script,
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
