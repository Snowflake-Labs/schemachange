import sys

from schemachange.deploy import deploy
from schemachange.render import render
from schemachange.Config import config_factory, RenderConfig, DeployConfig
from schemachange.SecretManager import SecretManager
from schemachange.get_yaml_config import get_yaml_config
from schemachange.parse_cli_args import parse_cli_args
from schemachange.session.SnowflakeSession import get_session_from_config

SCHEMACHANGE_VERSION = "3.6.1"
SNOWFLAKE_APPLICATION_NAME = "schemachange"


def get_merged_config() -> DeployConfig | RenderConfig:
    args = parse_cli_args(sys.argv[1:])
    cli_config = config_factory(args=args)
    yaml_config = get_yaml_config(
        subcommand=cli_config.subcommand,
        config_file_path=cli_config.config_file_path,
        script_path=getattr(cli_config, "script_path", None),
    )

    # override the YAML config with the CLI configuration
    return yaml_config.merge_exclude_unset(other=cli_config)


def main():
    print(f"schemachange version: {SCHEMACHANGE_VERSION}")

    config = get_merged_config()
    secret_manager = SecretManager(config_vars=config.vars)

    config.log_details(secret_manager=secret_manager)

    # Finally, execute the command
    if config.subcommand == "render":
        render(config=config, script_path=config.script_path)
    else:
        session = get_session_from_config(
            config=config,
            secret_manager=secret_manager,
            schemachange_version=SCHEMACHANGE_VERSION,
            snowflake_application_name=SNOWFLAKE_APPLICATION_NAME,
        )
        deploy(config=config, session=session)


if __name__ == "__main__":
    main()
