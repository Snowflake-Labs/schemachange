import hashlib
import logging
import sys
from pathlib import Path

import snowflake.connector
import structlog
from structlog import BoundLogger

from schemachange.config.get_merged_config import get_merged_config
from schemachange.config.RenderConfig import RenderConfig
from schemachange.deploy import deploy
from schemachange.JinjaTemplateProcessor import JinjaTemplateProcessor
from schemachange.redact_config_secrets import redact_config_secrets
from schemachange.session.SnowflakeSession import SnowflakeSession

# region Global Variables
# metadata
SCHEMACHANGE_VERSION = "4.1.0"
SNOWFLAKE_APPLICATION_NAME = "schemachange"
module_logger = structlog.getLogger(__name__)


def render(config: RenderConfig, script_path: Path, logger: BoundLogger) -> None:
    """
    Renders the provided script.

    Note: does not apply secrets filtering.
    """
    # Always process with jinja engine
    jinja_processor = JinjaTemplateProcessor(project_root=config.root_folder, modules_folder=config.modules_folder)
    content = jinja_processor.render(jinja_processor.relpath(script_path), config.config_vars)

    checksum = hashlib.sha224(content.encode("utf-8")).hexdigest()
    logger.info("Success", checksum=checksum, content=content)


def verify(config, logger: BoundLogger) -> None:
    """
    Verifies Snowflake connectivity and displays configuration parameters.

    Tests the connection to Snowflake using the provided configuration and
    reports the connection status along with the configuration parameters being used.
    """
    logger.info("=" * 80)
    logger.info("Schemachange Configuration Verification")
    logger.info("=" * 80)

    # Display schemachange-specific configuration
    logger.info("")
    logger.info("Schemachange Configuration:")
    logger.info(f"  Config File: {config.config_file_path}")
    logger.info(f"  Root Folder: {config.root_folder}")
    if config.modules_folder:
        logger.info(f"  Modules Folder: {config.modules_folder}")
    logger.info(f"  Log Level: {logging.getLevelName(config.log_level)}")
    logger.info(f"  Config Variables: {len(config.config_vars)} variable(s) defined")

    # Display deploy-specific configuration if available
    if hasattr(config, "change_history_table"):
        logger.info("")
        logger.info("Deploy Configuration:")
        logger.info(f"  Change History Table: {config.change_history_table}")
        logger.info(f"  Create Change History Table: {config.create_change_history_table}")
        logger.info(f"  Autocommit: {config.autocommit}")
        logger.info(f"  Dry Run: {config.dry_run}")
        if config.query_tag:
            logger.info(f"  Query Tag: {config.query_tag}")

    # Display Snowflake connection configuration
    session_kwargs = config.get_session_kwargs()
    logger.info("")
    logger.info("Snowflake Connection Configuration:")

    # Display connections.toml settings if used
    if session_kwargs.get("connections_file_path"):
        logger.info(f"  Connections File: {session_kwargs['connections_file_path']}")
    if session_kwargs.get("connection_name"):
        logger.info(f"  Connection Name: {session_kwargs['connection_name']}")

    # Display connection parameters (mask sensitive data)
    if session_kwargs.get("account"):
        logger.info(f"  Account: {session_kwargs['account']}")
    if session_kwargs.get("user"):
        logger.info(f"  User: {session_kwargs['user']}")
    if session_kwargs.get("role"):
        logger.info(f"  Role: {session_kwargs['role']}")
    if session_kwargs.get("warehouse"):
        logger.info(f"  Warehouse: {session_kwargs['warehouse']}")
    if session_kwargs.get("database"):
        logger.info(f"  Database: {session_kwargs['database']}")
    if session_kwargs.get("schema"):
        logger.info(f"  Schema: {session_kwargs['schema']}")
    if session_kwargs.get("authenticator"):
        logger.info(f"  Authenticator: {session_kwargs['authenticator']}")
    if session_kwargs.get("password"):
        logger.info("  Password: ****** (set)")
    if session_kwargs.get("token"):
        logger.info("  Token: ****** (set)")
    if session_kwargs.get("private_key_path"):
        logger.info(f"  Private Key Path: {session_kwargs['private_key_path']}")
    if session_kwargs.get("private_key_passphrase"):
        logger.info("  Private Key Passphrase: ****** (set)")

    # Test Snowflake connectivity
    logger.info("")
    logger.info("Testing Snowflake Connectivity...")
    logger.info("-" * 80)

    try:
        # Connect directly to Snowflake without SnowflakeSession
        # (SnowflakeSession requires change_history_table which verify doesn't need)

        # Prepare connection parameters
        connect_params = {}

        # Handle connections.toml if specified
        if session_kwargs.get("connections_file_path") and session_kwargs.get("connection_name"):
            connect_params["connections_file_path"] = str(session_kwargs["connections_file_path"])
            connect_params["connection_name"] = session_kwargs["connection_name"]

        # Add explicit connection parameters (these override connections.toml)
        for param in [
            "account",
            "user",
            "role",
            "warehouse",
            "database",
            "schema",
            "authenticator",
            "password",
            "token",
            "private_key_path",
            "private_key_passphrase",
        ]:
            if param in session_kwargs and session_kwargs[param] is not None:
                connect_params[param] = session_kwargs[param]

        # Add additional Snowflake parameters
        if session_kwargs.get("additional_snowflake_params"):
            for key, value in session_kwargs["additional_snowflake_params"].items():
                snake_case_key = key.replace("-", "_")
                connect_params[snake_case_key] = value

        # Set application identifier
        connect_params["application"] = f"{SNOWFLAKE_APPLICATION_NAME}_{SCHEMACHANGE_VERSION}"
        connect_params["session_parameters"] = {"QUERY_TAG": f"schemachange {SCHEMACHANGE_VERSION}"}

        # Connect
        con = snowflake.connector.connect(**connect_params)

        logger.info("")
        logger.info("✓ Connection Successful!")
        logger.info("")
        logger.info("Connection Details:")
        logger.info(f"  Account: {connect_params.get('account', 'N/A')}")
        logger.info(f"  User: {connect_params.get('user', 'N/A')}")
        logger.info(f"  Role: {connect_params.get('role', 'N/A')}")
        logger.info(f"  Warehouse: {connect_params.get('warehouse', 'N/A')}")
        logger.info(f"  Database: {connect_params.get('database', 'N/A')}")
        logger.info(f"  Schema: {connect_params.get('schema', 'N/A')}")
        logger.info(f"  Session ID: {con.session_id}")

        # Test a simple query
        logger.info("")
        logger.info("Testing Query Execution...")
        cursor = con.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        snowflake_version = cursor.fetchone()[0]
        cursor.close()
        logger.info(f"  Snowflake Version: {snowflake_version}")

        logger.info("")
        logger.info("=" * 80)
        logger.info("✓ Verification Complete - All checks passed!")
        logger.info("=" * 80)

        # Close the connection
        con.close()

    except snowflake.connector.errors.DatabaseError as e:
        logger.error("")
        logger.error("✗ Connection Failed!")
        logger.error(f"  Error: {str(e)}")
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("  - Verify your account name is correct")
        logger.error("  - Check that required connection parameters are provided")
        logger.error("  - Ensure you have network connectivity to Snowflake")
        logger.error("=" * 80)
        raise

    except snowflake.connector.errors.ProgrammingError as e:
        logger.error("")
        logger.error("✗ Authentication Failed!")
        logger.error(f"  Error: {str(e)}")
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("  - Verify your username and password/token are correct")
        logger.error("  - Check your authentication method (password, PAT, OAuth, JWT, etc.)")
        logger.error("  - Ensure your user account is not locked or expired")
        logger.error("  - For MFA-enabled accounts, use Programmatic Access Tokens (PATs)")
        logger.error("=" * 80)
        raise

    except Exception as e:
        logger.error("")
        logger.error("✗ Verification Failed!")
        logger.error(f"  Error: {str(e)}")
        logger.error("=" * 80)
        raise


def main():
    try:
        module_logger.info(f"schemachange version: {SCHEMACHANGE_VERSION}")

        config = get_merged_config(logger=module_logger)
        redact_config_secrets(config_secrets=config.secrets)

        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(config.log_level),
        )

        logger = structlog.getLogger()
        logger = logger.bind(schemachange_version=SCHEMACHANGE_VERSION)

        config.log_details()

        # Finally, execute the command
        if config.subcommand == "render":
            render(
                config=config,
                script_path=config.script_path,
                logger=logger,
            )
        elif config.subcommand == "verify":
            verify(
                config=config,
                logger=logger,
            )
        else:
            session = SnowflakeSession(
                schemachange_version=SCHEMACHANGE_VERSION,
                application=SNOWFLAKE_APPLICATION_NAME,
                logger=logger,
                **config.get_session_kwargs(),
            )
            deploy(config=config, session=session)

    except ValueError as e:
        module_logger.error("Configuration error", error=str(e), exc_info=True)
        sys.exit(1)
    except FileNotFoundError as e:
        module_logger.error("File not found", error=str(e), exc_info=True)
        sys.exit(1)
    except PermissionError as e:
        module_logger.error("Permission denied", error=str(e), exc_info=True)
        sys.exit(1)
    except snowflake.connector.errors.DatabaseError as e:
        module_logger.error("Snowflake connection error", error=str(e), exc_info=True)
        module_logger.error("Please check your Snowflake credentials and connection parameters.")
        module_logger.error("Use 'schemachange verify' to test your connection and view configuration.")
        sys.exit(1)
    except snowflake.connector.errors.ProgrammingError as e:
        module_logger.error("Snowflake authentication error", error=str(e), exc_info=True)
        module_logger.error("Please verify your account, username, and authentication method.")
        module_logger.error("Use 'schemachange verify' to test your connection and view configuration.")
        sys.exit(1)
    except KeyboardInterrupt:
        module_logger.warning("Operation cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        module_logger.error("Unexpected error", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
