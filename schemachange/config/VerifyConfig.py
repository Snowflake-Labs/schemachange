from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Literal

from schemachange.config.BaseConfig import BaseConfig
from schemachange.config.utils import (
    get_snowflake_authenticator,
    get_snowflake_identifier_string,
    get_snowflake_password,
    get_snowflake_private_key_passphrase,
    get_snowflake_private_key_path,
    get_snowflake_token_file_path,
)


@dataclasses.dataclass(frozen=True)
class VerifyConfig(BaseConfig):
    """
    Configuration for the verify subcommand.

    The verify command tests Snowflake connectivity and displays configuration
    parameters. It requires the same connection parameters as deploy but doesn't
    need deployment-specific settings like change_history_table.
    """

    subcommand: Literal["verify"] = "verify"
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_role: str | None = None
    snowflake_warehouse: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str | None = None
    connections_file_path: Path | None = None
    connection_name: str | None = None
    # Authentication parameters (CLI > ENV precedence)
    authenticator: str | None = None
    private_key_path: str | None = None
    private_key_passphrase: str | None = None
    token_file_path: str | None = None
    additional_snowflake_params: dict | None = None  # Parameters from YAML v2 or generic SNOWFLAKE_* env vars

    @classmethod
    def factory(
        cls,
        config_file_path: Path,
        **kwargs,
    ):
        if "subcommand" in kwargs:
            kwargs.pop("subcommand")

        # Filter out deployment-specific parameters that verify doesn't support
        # These are only relevant for the deploy command
        deployment_only_params = [
            "change_history_table",
            "create_change_history_table",
            "dry_run",
            "autocommit",
            "query_tag",
            "root_folder",
            "modules_folder",
            "vars",
        ]
        for param in deployment_only_params:
            kwargs.pop(param, None)

        # Validate Snowflake identifier strings
        for sf_input in [
            "snowflake_role",
            "snowflake_warehouse",
            "snowflake_database",
            "snowflake_schema",
        ]:
            if sf_input in kwargs and kwargs[sf_input] is not None:
                kwargs[sf_input] = get_snowflake_identifier_string(kwargs[sf_input], sf_input)

        return super().factory(
            subcommand="verify",
            config_file_path=config_file_path,
            **kwargs,
        )

    def get_session_kwargs(self) -> dict:
        """
        Get session kwargs for Snowflake connection.

        Similar to DeployConfig but without deployment-specific parameters.
        """
        session_kwargs = {
            "account": self.snowflake_account,
            "user": self.snowflake_user,
            "role": self.snowflake_role,
            "warehouse": self.snowflake_warehouse,
            "database": self.snowflake_database,
            "schema": self.snowflake_schema,
            "connections_file_path": self.connections_file_path,
            "connection_name": self.connection_name,
            "autocommit": False,  # Default for verify
            "query_tag": None,  # Not needed for verify
            "additional_snowflake_params": self.additional_snowflake_params,
        }

        # Add password from environment variable if available
        snowflake_password = get_snowflake_password()
        if snowflake_password is not None and snowflake_password:
            session_kwargs["password"] = snowflake_password

        # Add authentication parameters with priority: CLI/YAML > ENV
        authenticator = self.authenticator if self.authenticator is not None else get_snowflake_authenticator()
        if authenticator is not None:
            session_kwargs["authenticator"] = authenticator

        private_key_path = (
            self.private_key_path if self.private_key_path is not None else get_snowflake_private_key_path()
        )
        if private_key_path is not None:
            session_kwargs["private_key_path"] = private_key_path

        private_key_passphrase = (
            self.private_key_passphrase
            if self.private_key_passphrase is not None
            else get_snowflake_private_key_passphrase()
        )
        if private_key_passphrase is not None:
            session_kwargs["private_key_passphrase"] = private_key_passphrase

        # Read OAuth token from file if specified
        token_file_path = self.token_file_path if self.token_file_path is not None else get_snowflake_token_file_path()
        if token_file_path is not None:
            try:
                expanded_path = Path(token_file_path).expanduser()
                with open(expanded_path) as token_file:
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
