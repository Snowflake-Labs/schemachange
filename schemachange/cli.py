import sys
import textwrap
import yaml

from schemachange.deploy import deploy
from schemachange.render import render
from schemachange.extract_config_secrets import extract_config_secrets
from schemachange.Config import config_factory
from schemachange.SecretManager import SecretManager
from schemachange.get_yaml_config import get_yaml_config
from schemachange.parse_cli_args import parse_cli_args
from schemachange.session.Credential import credential_factory
from schemachange.session.SnowflakeSession import SnowflakeSession

SCHEMACHANGE_VERSION = "3.6.1"
SNOWFLAKE_APPLICATION_NAME = "schemachange"


def main():
    print(f"schemachange version: {SCHEMACHANGE_VERSION}")

    args = parse_cli_args(sys.argv[1:])
    cli_config = config_factory(args=args)
    yaml_config = get_yaml_config(
        subcommand=cli_config.subcommand,
        config_file_path=cli_config.config_file_path,
        script_path=getattr(cli_config, "script_path", None),
    )

    # override the YAML config with the CLI configuration
    config = yaml_config.merge_exclude_unset(other=cli_config)

    # set up a secret manager and assign to global scope
    sm = SecretManager()
    SecretManager.set_global_manager(sm)
    # Extract all secrets for --vars
    sm.add_range(extract_config_secrets(config))

    # Then log some details
    print(f"Using root folder {str(config.root_folder)}")
    if config.modules_folder:
        print(f"Using Jinja modules folder {str(config.modules_folder)}")

    # pretty print the variables in yaml style
    if not config.vars:
        print("Using variables: {}")
    else:
        print("Using variables:")
        print(
            textwrap.indent(
                SecretManager.global_redact(
                    yaml.dump(config.vars, sort_keys=False, default_flow_style=False)
                ),
                prefix="  ",
            )
        )

    # Finally, execute the command
    if config.subcommand == "render":
        render(config=config, script_path=config.script_path)
    else:
        config.check_for_deploy_args()
        credential = credential_factory(
            oauth_config=config.oauth_config, verbose=config.verbose
        )
        session = SnowflakeSession(
            config=config,
            snowflake_user=config.snowflake_user,
            snowflake_account=config.snowflake_account,
            snowflake_role=config.snowflake_role,
            schemachange_version=SCHEMACHANGE_VERSION,
            snowflake_application_name=SNOWFLAKE_APPLICATION_NAME,
            credential=credential,
            snowflake_warehouse=config.snowflake_warehouse,
            snowflake_database=config.snowflake_database,
            snowflake_schema=config.snowflake_schema,
            query_tag=config.query_tag,
        )
        deploy(config=config, session=session)


if __name__ == "__main__":
    main()
