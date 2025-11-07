# Demo

The contents of this Demo serves two audiences - Consumers and Contributors. For the Consumer, the demo provides a basis
to see how schemachange works with the main feature set. For the contributor, who forks the repo and submits PRs to the
codebase, this will serve as a basis to test the PR against your own snowflake account to ensure your code change does
not break any existing functionality.

## Prerequisites

- You will need your own snowflake Account to test the Demo - Both as a contributor and consumer.
- You will need to review and run statements in the provision folder or set up your own database and schema.
    - [initialize.sql](provision/initialize.sql): Contains the SQL variables to initialize your environment.
    - [setup_schemachange_schema.sql](provision/setup_schemachange_schema.sql): Contains the SQL variables to track the
      individual demo scenarios in its own change history table.

## Environment Variable Support (Version 4.1.0+)

Starting with version 4.1.0, schemachange natively supports `SNOWFLAKE_*` environment variables for all connection and authentication parameters. This eliminates the need for workarounds like `populateConnection.sh` or `connections.toml` generation scripts.

### Configuration Priority Order

Schemachange uses the following priority order when loading configuration (highest priority first):

1. **CLI arguments** - Explicitly provided command-line flags
2. **Environment variables** - `SNOWFLAKE_*` prefixed variables
3. **YAML configuration file** - `schemachange-config.yml`
4. **Snowflake connections.toml** - Snowflake Python Connector's connection file

This means you can:
- Set base configuration in `connections.toml` or YAML
- Override with environment variables for CI/CD
- Further override with CLI arguments for specific runs

### Supported Environment Variables

#### Connection Parameters
- `SNOWFLAKE_ACCOUNT` - Snowflake account identifier
- `SNOWFLAKE_USER` - Username for authentication
- `SNOWFLAKE_PASSWORD` - Password for authentication
- `SNOWFLAKE_ROLE` - Role to use after connecting
- `SNOWFLAKE_WAREHOUSE` - Default warehouse
- `SNOWFLAKE_DATABASE` - Default database
- `SNOWFLAKE_SCHEMA` - Default schema

#### Authentication Parameters
- `SNOWFLAKE_AUTHENTICATOR` - Authentication method (e.g., `snowflake`, `oauth`, `externalbrowser`, `snowflake_jwt`)
- `SNOWFLAKE_PRIVATE_KEY_PATH` - Path to private key file for key-pair authentication
- `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` - Passphrase for encrypted private key
- `SNOWFLAKE_TOKEN_FILE_PATH` - Path to OAuth token file (for external OAuth only, NOT for PAT)

#### Configuration Parameters
- `SNOWFLAKE_CONNECTIONS_FILE_PATH` - Custom path to `connections.toml`
- `SNOWFLAKE_HOME` - Custom Snowflake home directory
- `SNOWFLAKE_DEFAULT_CONNECTION_NAME` - Default connection name from `connections.toml`

### Example Usage

#### Basic Password Authentication
```bash
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="demo_user"
export SNOWFLAKE_PASSWORD="secure_password"
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

# Run schemachange - it will automatically pick up the environment variables
schemachange deploy --config-folder ./demo/basics_demo
```

#### Key-Pair Authentication
```bash
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="demo_user"
export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
export SNOWFLAKE_PRIVATE_KEY_PATH="~/.ssh/snowflake_key.p8"
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE="key_password"
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

schemachange deploy --config-folder ./demo/basics_demo
```

#### Programmatic Access Token (PAT) Authentication
**Recommended for CI/CD and service accounts** - especially with Snowflake's MFA enforcement (November 2025).

```bash
# First, generate a PAT in Snowflake (via Snowsight or SQL):
# ALTER USER service_account ADD PROGRAMMATIC ACCESS TOKEN my_token_name;

# Option 1: Store PAT in a file and read it
echo "your_generated_token_here" > ~/.snowflake/pat_token.txt
chmod 600 ~/.snowflake/pat_token.txt

export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="service_account"
export SNOWFLAKE_PASSWORD=$(cat ~/.snowflake/pat_token.txt)
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

schemachange deploy --config-folder ./demo/basics_demo

# Option 2: Set PAT directly (for CI/CD secrets)
export SNOWFLAKE_PASSWORD="<your_pat_token_value>"
# ... other exports ...
schemachange deploy --config-folder ./demo/basics_demo
```

**Note:** PATs use the default `snowflake` authenticator - no need to set `SNOWFLAKE_AUTHENTICATOR`. The Snowflake connector automatically detects that the password value is a PAT.

#### External Browser (SSO) Authentication
```bash
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="demo_user"
export SNOWFLAKE_AUTHENTICATOR="externalbrowser"
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

schemachange deploy --config-folder ./demo/basics_demo
```

### Deprecation Notice

⚠️ **SNOWSQL_PWD is deprecated**: The legacy `SNOWSQL_PWD` environment variable is deprecated in favor of `SNOWFLAKE_PASSWORD`. While `SNOWSQL_PWD` is still supported for backward compatibility, you will see a deprecation warning. Please migrate to `SNOWFLAKE_PASSWORD`.

## Interactive Authentication Examples

The `examples/` directory contains ready-to-use scripts for testing different authentication methods. These interactive scripts will guide you through the authentication process and help you verify your configuration.

### Quick Start

```bash
cd demo/examples

# Choose your authentication method:
./password_auth_example.sh          # Basic password authentication
./pat_auth_example.sh              # Programmatic Access Token (RECOMMENDED for CI/CD)
./keypair_auth_example.sh          # RSA key-pair authentication (RECOMMENDED for CI/CD)
./sso_auth_example.sh              # Browser-based SSO authentication
```

Each script will:
- Guide you through the authentication setup process
- Prompt for required credentials interactively
- Validate your connection by rendering a test script
- Provide helpful troubleshooting tips if authentication fails
- Show next steps for deploying to the demo projects

### What's Included

The examples directory contains:

- **`README.md`** - Comprehensive guide to all authentication methods
- **`password_auth_example.sh`** - Password authentication example
- **`pat_auth_example.sh`** - PAT authentication example (uses `SNOWFLAKE_PASSWORD`)
- **`keypair_auth_example.sh`** - Key-pair authentication with key generation guide
- **`sso_auth_example.sh`** - SSO authentication with browser integration
- **`templates/`** - Credential file templates for easy setup
  - `token.txt.template` - Token file template (for PAT or OAuth storage)
  - `connections.toml.template` - Snowflake connections file template

### Example Output

When you run an authentication example, you'll see:

```
╔════════════════════════════════════════════════════════════╗
║  Schemachange - PAT Authentication Example               ║
║  (Recommended for CI/CD and Service Accounts)             ║
╚════════════════════════════════════════════════════════════╝

Configuration:
  Account:        myaccount.us-east-1
  User:           service_account
  Password:       [PAT SET]
  Role:           SCHEMACHANGE_DEMO-DEPLOY
  Warehouse:      SCHEMACHANGE_DEMO_WH
  Database:       SCHEMACHANGE_DEMO
  Project:        basics_demo

Testing connection with 'schemachange render'...

✓ Success! PAT authentication is working.
```

For detailed documentation, see [examples/README.md](examples/README.md).

### Consumers

- If you are consumer who is installing schemachange and wants to test-run the demo, then you will have to set the
  following environment variables.
    - SNOWFLAKE_ACCOUNT: This will be the account identifier for your Snowflake account.
    - SNOWFLAKE_USER: This will be the user that will connect to your Snowflake account (`SNOWFLAKE_ACCOUNT`).
    - SNOWFLAKE_PASSWORD: This is the password for the user (`SNOWFLAKE_USER`) that will connect to your Snowflake
      account (`SNOWFLAKE_ACCOUNT`).
    - SCENARIO_NAME: This will be demo folder you intend to experiment with. For
      starters, `basics_demo`, `citibike_demo` or `citibike_demo_jinja` are included with the repo that will set the
      root folder value in the respective schemachange-config.yml file.
    - SNOWFLAKE_WAREHOUSE: This will be the warehouse you set up for the demo in your Snowflake
      account (`SNOWFLAKE_ACCOUNT`). Default setup is SCHEMACHANGE_DEMO_WH.
    - SNOWFLAKE_DATABASE Keyed to SCHEMACHANGE_DEMO. You can update this to the database in your snowflake account
      (`SNOWFLAKE_ACCOUNT`). You will also need to update the provision scripts accordingly.
    - SNOWFLAKE_ROLE Keyed to SCHEMACHANGE_DEMO-DEPLOY. This particular role name was chosen to test hyphenated roles
      in schemachange. You can update this value to match the role you have setup in your snowflake
      account (`SNOWFLAKE_ACCOUNT`).

The scripts in the `provision` folder can be used to set up up your demo database along with a schema in that database
that will house the change tracking tables needed to set up and teardown the schemas used to test a working version of
the demo DDL scripts.

- The [initialize](provision/initialize.sql) script setups the database, warehouse and account level access roles that
  will be used on the
- The [setup](provision/setup_schemachange_schema.sql) script creates the `SCHEMACHANGE` schema in the database that you
  created in the initialize step.

### Contributors

1. Execute the [initialize.sql](provision/initialize.sql)
   and [setup_schemachange_schema.sql](provision/setup_schemachange_schema.sql) scripts to create up a
   `SCHEMACHANGE_DEMO`
   database and `SCHEMACHANGE` schema (See [Prerequisites](#prerequisites)).

2. Create the
   following [GitHub Action Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
   in your forked repository. GitHub will use these actions to set up and teardown the temporary schema(s) it creates to
   test your code.

    - `SCHEMACHANGE_SNOWFLAKE_PASSWORD`
    - `SCHEMACHANGE_SNOWFLAKE_USER`
    - `SCHEMACHANGE_SNOWFLAKE_ACCOUNT`

# Setup

The setup scripts are included to build the schema needed by the GitHub Actions Workflow to avoid conflict across jobs
when tested in parallel. The Setup script will create a new schema to run the schemachange script for the corresponding
scenario.

# Teardown

The Teardown scripts are the bookend pairing of the Setup script for each scenario so that when the build process is
done using GitHub actions, you will have a log of the testing done to ensure that schemachange is working as expected.
