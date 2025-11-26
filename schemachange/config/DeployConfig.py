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
    get_snowflake_private_key_file,
    get_snowflake_private_key_file_pwd,
    get_snowflake_private_key_passphrase,
    get_snowflake_private_key_path,
    get_snowflake_token_file_path,
)


@dataclasses.dataclass(frozen=True)
class DeployConfig(BaseConfig):
    subcommand: Literal["deploy"] = "deploy"
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_role: str | None = None
    snowflake_warehouse: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str | None = None
    connections_file_path: Path | None = None
    connection_name: str | None = None
    change_history_table: ChangeHistoryTable | None = dataclasses.field(default_factory=ChangeHistoryTable)
    create_change_history_table: bool = False
    autocommit: bool = False
    dry_run: bool = False
    query_tag: str | None = None
    # Authentication parameters - All Snowflake connector params use snowflake_ prefix internally
    # (Prefix is stripped when building connect_kwargs)
    snowflake_authenticator: str | None = None
    snowflake_private_key_path: str | None = None  # DEPRECATED - use snowflake_private_key_file
    snowflake_private_key_file: str | None = None  # Recommended (matches Snowflake connector)
    snowflake_private_key_passphrase: str | None = None  # DEPRECATED - use snowflake_private_key_file_pwd
    snowflake_private_key_file_pwd: str | None = None  # Recommended (matches Snowflake connector)
    snowflake_token_file_path: str | None = None
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

        for sf_input in [
            "snowflake_role",
            "snowflake_warehouse",
            "snowflake_database",
            "snowflake_schema",
        ]:
            if sf_input in kwargs and kwargs[sf_input] is not None:
                kwargs[sf_input] = get_snowflake_identifier_string(kwargs[sf_input], sf_input)

        # Convert connections_file_path to Path object and expand ~ if needed
        if "connections_file_path" in kwargs and kwargs["connections_file_path"] is not None:
            kwargs["connections_file_path"] = Path(kwargs["connections_file_path"]).expanduser()

        change_history_table = ChangeHistoryTable.from_str(table_str=change_history_table)

        return super().factory(
            subcommand="deploy",
            config_file_path=config_file_path,
            change_history_table=change_history_table,
            **kwargs,
        )

    def get_session_kwargs(self) -> dict:
        session_kwargs = {
            "account": self.snowflake_account,
            "user": self.snowflake_user,
            "role": self.snowflake_role,
            "warehouse": self.snowflake_warehouse,
            "database": self.snowflake_database,
            "schema": self.snowflake_schema,
            # NOTE: connections_file_path and connection_name are NOT passed to SnowflakeSession
            # All parameters from connections.toml have already been merged in get_merged_config.py
            # NOTE: change_history_table is now passed explicitly in cli.py, not via get_session_kwargs()
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

        # Add authentication parameters with priority: Config (CLI/ENV/YAML/connections.toml merged) > ENV fallback
        # These are used for OAuth, JWT, and other auth methods
        # Note: Field names have snowflake_ prefix internally, but we strip it for connect()

        # Authenticator: Use merged config value, fallback to ENV
        authenticator = (
            self.snowflake_authenticator if self.snowflake_authenticator is not None else get_snowflake_authenticator()
        )
        if authenticator is not None:
            session_kwargs["authenticator"] = authenticator

        # Private key file: Priority is Config (new/old) > ENV (new/old)
        private_key_file = None
        used_deprecated_key_path = False

        # Check config first (new name, then old name)
        if self.snowflake_private_key_file is not None:
            private_key_file = self.snowflake_private_key_file
        elif self.snowflake_private_key_path is not None:
            private_key_file = self.snowflake_private_key_path
            used_deprecated_key_path = True

        # If not in config, check ENV (new name, then old name)
        if private_key_file is None:
            env_new = get_snowflake_private_key_file()
            if env_new is not None:
                private_key_file = env_new
            else:
                env_old = get_snowflake_private_key_path()
                if env_old is not None:
                    private_key_file = env_old
                    used_deprecated_key_path = True

        # Show deprecation warning if old name was actually used
        if used_deprecated_key_path and private_key_file is not None:
            import warnings

            warnings.warn(
                "DEPRECATION WARNING: 'private_key_path' is deprecated. "
                "Please use 'private_key_file' instead to match the Snowflake Python Connector parameter name. "
                "Update your configuration:\n"
                "  - CLI: Use --snowflake-private-key-file instead of --snowflake-private-key-path\n"
                "  - ENV: Use SNOWFLAKE_PRIVATE_KEY_FILE instead of SNOWFLAKE_PRIVATE_KEY_PATH\n"
                "  - connections.toml: Use private_key_file instead of private_key_path\n"
                "  - YAML: Use snowflake-private-key-file instead of snowflake-private-key-path\n"
                "'private_key_path' will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )

        if private_key_file is not None:
            # Expand ~ to home directory if present (preserves path separators otherwise)
            if "~" in private_key_file:
                session_kwargs["private_key_file"] = str(Path(private_key_file).expanduser())
            else:
                session_kwargs["private_key_file"] = private_key_file

        # Private key passphrase: Priority is Config (new/old) > ENV (new/old)
        private_key_pwd = None
        used_deprecated_passphrase = False

        # Check config first (new name, then old name)
        if self.snowflake_private_key_file_pwd is not None:
            private_key_pwd = self.snowflake_private_key_file_pwd
        elif self.snowflake_private_key_passphrase is not None:
            private_key_pwd = self.snowflake_private_key_passphrase
            used_deprecated_passphrase = True

        # If not in config, check ENV (new name, then old name)
        if private_key_pwd is None:
            env_new = get_snowflake_private_key_file_pwd()
            if env_new is not None:
                private_key_pwd = env_new
            else:
                env_old = get_snowflake_private_key_passphrase()
                if env_old is not None:
                    private_key_pwd = env_old
                    used_deprecated_passphrase = True

        # Show deprecation warning if old name was actually used
        if used_deprecated_passphrase and private_key_pwd is not None:
            import warnings

            warnings.warn(
                "DEPRECATION WARNING: 'private_key_passphrase' is deprecated. "
                "Please use 'private_key_file_pwd' instead to match the Snowflake Python Connector parameter name. "
                "Update your configuration:\n"
                "  - ENV: Use SNOWFLAKE_PRIVATE_KEY_FILE_PWD instead of SNOWFLAKE_PRIVATE_KEY_PASSPHRASE\n"
                "  - connections.toml: Use private_key_file_pwd instead of private_key_passphrase\n"
                "  - YAML: Use snowflake-private-key-file-pwd instead of snowflake-private-key-passphrase\n"
                "'private_key_passphrase' will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )

        if private_key_pwd is not None:
            # Map to Snowflake connector's parameter name
            session_kwargs["private_key_file_pwd"] = private_key_pwd

        # Read OAuth token from file if specified
        # NOTE: SNOWFLAKE_TOKEN_FILE_PATH is for OAUTH ONLY (external OAuth providers)
        #       It should be used with SNOWFLAKE_AUTHENTICATOR=oauth
        #       For PATs, use SNOWFLAKE_PASSWORD instead (see above)
        # Token file path: Use merged config value, fallback to ENV
        token_file_path = (
            self.snowflake_token_file_path
            if self.snowflake_token_file_path is not None
            else get_snowflake_token_file_path()
        )
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
