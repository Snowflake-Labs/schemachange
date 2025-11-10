from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Literal

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable
from schemachange.config.utils import (
    get_snowflake_authenticator,
    get_snowflake_identifier_string,
    get_snowflake_password,
    get_snowflake_private_key_passphrase,
    get_snowflake_private_key_path,
    get_snowflake_token_file_path,
)


@dataclasses.dataclass(frozen=True)
class DeployConfig(BaseConfig):
    subcommand: Literal["deploy"] = "deploy"
    snowflake_account: str | None = None  # TODO: Remove when connections.toml is enforced
    snowflake_user: str | None = None  # TODO: Remove when connections.toml is enforced
    snowflake_role: str | None = None  # TODO: Remove when connections.toml is enforced
    snowflake_warehouse: str | None = None  # TODO: Remove when connections.toml is enforced
    snowflake_database: str | None = None  # TODO: Remove when connections.toml is enforced
    snowflake_schema: str | None = None  # TODO: Remove when connections.toml is enforced
    connections_file_path: Path | None = None
    connection_name: str | None = None
    # TODO: Turn change_history_table into three arguments. There's no need to parse it from a string
    change_history_table: ChangeHistoryTable | None = dataclasses.field(default_factory=ChangeHistoryTable)
    create_change_history_table: bool = False
    autocommit: bool = False
    dry_run: bool = False
    query_tag: str | None = None
    # Authentication parameters (CLI > ENV precedence)
    authenticator: str | None = None
    private_key_path: str | None = None
    private_key_passphrase: str | None = None
    token_file_path: str | None = None
    version_number_validation_regex: str | None = None
    raise_exception_on_ignored_versioned_script: bool = False
    session_parameters: dict | None = None  # Session parameters from CLI/ENV/YAML (merged with connections.toml)
    additional_snowflake_params: dict | None = None  # Parameters from YAML v2 or generic SNOWFLAKE_* env vars

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
                kwargs[sf_input] = get_snowflake_identifier_string(kwargs[sf_input], sf_input)

        change_history_table = ChangeHistoryTable.from_str(table_str=change_history_table)

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
            "query_tag": self.query_tag,
            "session_parameters": self.session_parameters,
            "additional_snowflake_params": self.additional_snowflake_params,
        }

        # Add password from environment variable if available
        # NOTE: SNOWFLAKE_PASSWORD is used for:
        #   1. Traditional password authentication (deprecated with MFA requirements)
        #   2. Programmatic Access Tokens (PATs) - recommended for CI/CD
        #      PATs use the default 'snowflake' authenticator (no need to set SNOWFLAKE_AUTHENTICATOR)
        snowflake_password = get_snowflake_password()
        if snowflake_password is not None and snowflake_password:
            session_kwargs["password"] = snowflake_password

        # Add authentication parameters with priority: CLI/YAML > ENV
        # These are used for OAuth, JWT, and other auth methods

        # Authenticator: CLI/YAML takes precedence over ENV
        authenticator = self.authenticator if self.authenticator is not None else get_snowflake_authenticator()
        if authenticator is not None:
            session_kwargs["authenticator"] = authenticator

        # Private key path: CLI/YAML takes precedence over ENV
        private_key_path = (
            self.private_key_path if self.private_key_path is not None else get_snowflake_private_key_path()
        )
        if private_key_path is not None:
            session_kwargs["private_key_path"] = private_key_path

        # Private key passphrase: CLI/YAML takes precedence over ENV
        private_key_passphrase = (
            self.private_key_passphrase
            if self.private_key_passphrase is not None
            else get_snowflake_private_key_passphrase()
        )
        if private_key_passphrase is not None:
            session_kwargs["private_key_passphrase"] = private_key_passphrase

        # Read OAuth token from file if specified
        # NOTE: SNOWFLAKE_TOKEN_FILE_PATH is for OAUTH ONLY (external OAuth providers)
        #       It should be used with SNOWFLAKE_AUTHENTICATOR=oauth
        #       For PATs, use SNOWFLAKE_PASSWORD instead (see above)
        # Token file path: CLI/YAML takes precedence over ENV
        token_file_path = self.token_file_path if self.token_file_path is not None else get_snowflake_token_file_path()
        if token_file_path is not None:
            try:
                # Expand user paths like ~/tokens/oauth.token
                expanded_path = Path(token_file_path).expanduser()
                with open(expanded_path) as token_file:
                    # Read and strip whitespace/newlines from token
                    token = token_file.read().strip()
                    if token:
                        session_kwargs["token"] = token
                    else:
                        raise ValueError(f"Token file is empty: {token_file_path}")
            except FileNotFoundError:
                raise FileNotFoundError(f"Token file not found: {token_file_path}") from None
            except PermissionError:
                raise PermissionError(f"Permission denied reading token file: {token_file_path}") from None
            except Exception as e:
                raise ValueError(f"Error reading token file {token_file_path}: {str(e)}") from e

        return {k: v for k, v in session_kwargs.items() if v is not None}
