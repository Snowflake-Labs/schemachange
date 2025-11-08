# schemachange

<img src="https://github.com/user-attachments/assets/8bc170c9-4171-48c7-812c-6d76c07ee364" alt="schemachange" title="schemachange logo" width="600" />

*Looking for snowchange? You've found the right spot. snowchange has been renamed to schemachange.*

[![pytest](https://github.com/Snowflake-Labs/schemachange/actions/workflows/master-pytest.yml/badge.svg)](https://github.com/Snowflake-Labs/schemachange/actions/workflows/master-pytest.yml)
[![PyPI](https://img.shields.io/pypi/v/schemachange.svg)](https://pypi.org/project/schemachange)

## Overview

schemachange is a simple python based tool to manage all of your [Snowflake](https://www.snowflake.com/) objects. It
follows an Imperative-style approach to Database Change Management (DCM) and was inspired by
the [Flyway database migration tool](https://www.red-gate.com/products/flyway/community/). When combined with a version control system and a CI/CD
tool, database changes can be approved and deployed through a pipeline using modern software delivery practices. As such
schemachange plays a critical role in enabling Database (or Data) DevOps.

DCM tools (also known as Database Migration, Schema Change Management, or Schema Migration tools) follow one of two
approaches: Declarative or Imperative. For a background on Database DevOps, including a discussion on the differences
between the Declarative and Imperative approaches, please read
the [Embracing Agile Software Delivery and DevOps with Snowflake](https://www.snowflake.com/blog/embracing-agile-software-delivery-and-devops-with-snowflake/)
blog post.

For the complete list of changes made to schemachange check out the [CHANGELOG](CHANGELOG.md).

To learn more about making a contribution to schemachange, please see our [Contributing guide](.github/CONTRIBUTING.md).

**Please note** that schemachange is a community-developed tool, not an official Snowflake offering. It comes with no
support or warranty.

## Table of Contents

1. [Overview](#overview)
1. [Project Structure](#project-structure)
    1. [Folder Structure](#folder-structure)
1. [Change Scripts](#change-scripts)
    1. [Versioned Script Naming](#versioned-script-naming)
    1. [Repeatable Script Naming](#repeatable-script-naming)
    1. [Always Script Naming](#always-script-naming)
    1. [Script Requirements](#script-requirements)
    1. [Using Variables in Scripts](#using-variables-in-scripts)
        1. [Secrets filtering](#secrets-filtering)
    1. [Jinja templating engine](#jinja-templating-engine)
    1. [Gotchas](#gotchas)
1. [Change History Table](#change-history-table)
1. [Authentication](#authentication)
    1. [Password Authentication](#password-authentication)
    1. [External OAuth Authentication](#external-oauth-authentication)
    1. [External Browser Authentication](#external-browser-authentication)
    1. [Okta Authentication](#okta-authentication)
    1. [Private Key Authentication](#private-key-authentication)
1. [Configuration](#configuration)
    1. [connections.toml File](#connectionstoml-file)
    1. [YAML Config File](#yaml-config-file)
        1. [Yaml Jinja support](#yaml-jinja-support)
    1. [Environment Variables](#environment-variables)
    1. [Configuration Priority](#configuration-priority)
1. [Commands](#commands)
    1. [deploy](#deploy)
    1. [render](#render)
1. [Running schemachange](#running-schemachange)
    1. [Prerequisites](#prerequisites)
    1. [Running the Script](#running-the-script)
1. [Integrating With DevOps](#integrating-with-devops)
    1. [Sample DevOps Process Flow](#sample-devops-process-flow)
    1. [Using in a CI/CD Pipeline](#using-in-a-cicd-pipeline)
1. [Maintainers](#maintainers)
1. [Third Party Packages](#third-party-packages)
1. [Legal](#legal)

## Project Structure

### Folder Structure

schemachange expects a directory structure like the following to exist:

```
(project_root)
|
|-- folder_1
    |-- V1.1.1__first_change.sql
    |-- V1.1.2__second_change.sql
    |-- R__sp_add_sales.sql
    |-- R__fn_get_timezone.sql
|-- folder_2
    |-- folder_3
        |-- V1.1.3__third_change.sql
        |-- R__fn_sort_ascii.sql
```

The schemachange folder structure is very flexible. The `project_root` folder is specified with the `-f`,
`--schemachange-root-folder`, or `--root-folder` argument. schemachange only pays attention to the filenames, not the paths. Therefore, under
the `project_root` folder you are free to arrange the change scripts any way you see fit. You can have as many
subfolders (and nested subfolders) as you would like.

## Change Scripts

### Versioned Script Naming

Versioned change scripts follow a similar naming convention to that used
by [Flyway Versioned Migrations](https://documentation.red-gate.com/fd/versioned-migrations-273973333.html). The script name
must follow this pattern (image taken
from [Flyway docs](https://documentation.red-gate.com/fd/versioned-migrations-273973333.html)):

<img src="https://github.com/user-attachments/assets/a71297d9-4a3c-4d30-82d3-c634be88fe54" alt="Flyway naming conventions" title="Flyway naming conventions" width="300" />

With the following rules for each part of the filename:

* **Prefix**: The letter 'V' for versioned change
* **Version**: A unique version number with dots or underscores separating as many number parts as you like
* **Separator**: __ (two underscores)
* **Description**: An arbitrary description with words separated by underscores or spaces (can not include two
  underscores)
* **Suffix**: .sql or .sql.jinja

For example, a script name that follows this convention is: `V1.1.1__first_change.sql`. As with Flyway, the unique
version string is very flexible. You just need to be consistent and always use the same convention, like 3 sets of
numbers separated by periods. Here are a few valid version strings:

* 1.1
* 1_1
* 1.2.3
* 1_2_3

Every script within a database folder must have a unique version number. schemachange will check for duplicate version
numbers and throw an error if it finds any. This helps to ensure that developers who are working in parallel don't
accidentally (re-)use the same version number.

### Repeatable Script Naming

Repeatable change scripts follow a similar naming convention to that used
by [Flyway Versioned Migrations](https://documentation.red-gate.com/fd/repeatable-migrations-273973335.html). The
script name must follow this pattern (image taken
from [Flyway docs](https://documentation.red-gate.com/fd/repeatable-migrations-273973335.html):

<img src="https://github.com/user-attachments/assets/06abd883-58b7-42d5-97b2-581158d8b121" alt="Flyway naming conventions" title="Flyway naming conventions" width="300" />

e.g:

* R__sp_add_sales.sql
* R__fn_get_timezone.sql
* R__fn_sort_ascii.sql

All repeatable change scripts are applied each time the utility is run, if there is a change in the file.
Repeatable scripts could be used for maintaining code that always needs to be applied in its entirety. e.g. stores
procedures, functions and view definitions etc.

Just like Flyway, within a single migration run, repeatable scripts are always applied after all pending versioned
scripts have been executed. Repeatable scripts are applied in alphabetical order of their description.

### Always Script Naming

Always change scripts are executed with every run of schemachange. This is an addition to the implementation
of [Flyway Versioned Migrations](https://documentation.red-gate.com/fd/versioned-migrations-273973333.html).
The script name must follow this pattern:

`A__Some_description.sql`

e.g.

* A__add_user.sql
* A__assign_roles.sql

This type of change script is useful for an environment set up after cloning. Always scripts are applied always last.

### Script Requirements

schemachange is designed to be very lightweight and not impose too many limitations. Each change script can have any
number of SQL statements within it and must supply the necessary context, like database and schema names. The context
can be supplied by using an explicit `USE <DATABASE>` command or by naming all objects with a three-part
name (`<database name>.<schema name>.<object name>`). schemachange will simply run the contents of each script against
the target Snowflake account, in the correct order. After each script, Schemachange will execute "reset" the context (
role, warehouse, database, schema) to the values used to configure the connector.

### Using Variables in Scripts

schemachange supports the jinja engine for a variable replacement strategy. One important use of variables is to support
multiple environments (dev, test, prod) in a single Snowflake account by dynamically changing the database name during
deployment. To use a variable in a change script, use this syntax anywhere in the script: `{{ variable1 }}`.

To pass variables to schemachange, check out the [Configuration](#configuration) section below. You can either use
the `--vars` command line parameter or the YAML config file `schemachange-config.yml`. For the command line version you
can pass variables like this: `--vars '{"variable1": "value", "variable2": "value2"}'`. This parameter accepts a flat
JSON object formatted as a string.

> *Nested objects and arrays don't make sense at this point and aren't supported.*

schemachange will replace any variable placeholders before running your change script code and will throw an error if it
finds any variable placeholders that haven't been replaced.

#### Secrets filtering

While many CI/CD tools already have the capability to filter secrets, it is best that any tool also does not output
secrets to the console or logs. Schemachange implements secrets filtering in a number of areas to ensure secrets are not
writen to the console or logs. The only exception is the `render` command which will display secrets.

A secret is just a standard variable that has been tagged as a secret. This is determined using a naming convention and
either of the following will tag a variable as a secret:

1. The variable name has the word `secret` in it.
   ```yaml
      config-version: 1
      vars:
         bucket_name: S3://......  # not a secret
         secret_key: 567576D8E  # a secret
   ```
2. The variable is a child of a key named `secrets`.
   ```yaml
      config-version: 1
      vars:
      secrets:
         my_key: 567576D8E # a secret
      aws:
         bucket_name: S3://......  # not a secret
         secrets:
            encryption_key: FGDSUUEHDHJK # a secret
            us_east_1:
               encryption_key: sdsdsd # a secret
   ```

### Jinja templating engine

schemachange uses the Jinja templating engine internally and
supports: [expressions](https://jinja.palletsprojects.com/en/3.0.x/templates/#expressions), [macros](https://jinja.palletsprojects.com/en/3.0.x/templates/#macros), [includes](https://jinja.palletsprojects.com/en/3.0.x/templates/#include)
and [template inheritance](https://jinja.palletsprojects.com/en/3.0.x/templates/#template-inheritance).

These files can be stored in the root-folder but schemachange also provides a separate modules
folder `--modules-folder`. This allows common logic to be stored outside of the main changes scripts.
The [demo/citibike_demo_jinja](demo/citibike_demo_jinja) has a simple example that demonstrates this.

schemachange uses Jinja's [`PrefixLoader`](https://jinja.palletsprojects.com/en/stable/api/#jinja2.PrefixLoader), so
regardless of the `--modules-folder` that's used, the file paths (such as those passed to [`include`](https://jinja.palletsprojects.com/en/stable/templates/#include))
should be prefixed with `modules/`.

The Jinja auto-escaping feature is disabled in schemachange, this feature in Jinja is currently designed for where the
output language is HTML/XML. So if you are using schemachange with untrusted inputs you will need to handle this within
your change scripts.

### Gotchas

Within change scripts:

- [Snowflake Scripting blocks need delimiters](https://docs.snowflake.com/en/developer-guide/snowflake-scripting/running-examples#introduction)
- [The last line can't be a comment](https://github.com/Snowflake-Labs/schemachange/issues/130)

## Change History Table

schemachange records all applied changes scripts to the change history table. By default, schemachange will attempt to
log all activities to the `METADATA.SCHEMACHANGE.CHANGE_HISTORY` table. The name and location of the change history
table can be overriden via a command line argument (`-c`, `--schemachange-change-history-table`, or `--change-history-table`)
or the `schemachange-config.yml` file (`change-history-table`). The value passed to the parameter can have a one, two, or
three part name (e.g. "TABLE_NAME", or "SCHEMA_NAME.TABLE_NAME", or "DATABASE_NAME.SCHEMA_NAME.TABLE_NAME"). This can be
used to support multiple environments (dev, test, prod) or multiple subject areas within the same Snowflake account.

By default, schemachange will not try to create the change history table, and it will fail if the table does not exist.
This behavior can be altered by passing in the `--schemachange-create-change-history-table` or `--create-change-history-table`
argument or adding `create-change-history-table: true` to the `schemachange-config.yml` file. Even with the
`--create-change-history-table` parameter, schemachange will not attempt to create the database for the change history
table. That must be created before running schemachange.

The structure of the `CHANGE_HISTORY` table is as follows:

| Column Name    | Type          | Example                       |
|----------------|---------------|-------------------------------|
| VERSION        | VARCHAR       | 1.1.1                         |
| DESCRIPTION    | VARCHAR       | First change                  |
| SCRIPT         | VARCHAR       | V1.1.1__first_change.sql      |
| SCRIPT_TYPE    | VARCHAR       | V                             |
| CHECKSUM       | VARCHAR       | 38e5ba03b1a6d2...             |
| EXECUTION_TIME | NUMBER        | 4                             |
| STATUS         | VARCHAR       | Success                       |
| INSTALLED_BY   | VARCHAR       | SNOWFLAKE_USER                |
| INSTALLED_ON   | TIMESTAMP_LTZ | 2020-03-17 12:54:33.056 -0700 |

A new row will be added to this table every time a change script has been applied to the database. schemachange will use
this table to identify which changes have been applied to the database and will not apply the same version more than
once.

Here is the current schema DDL for the change history table (found in the [schemachange/cli.py](schemachange/cli.py)
script), in case you choose to create it manually and not use the `--create-change-history-table` parameter:

```sql
CREATE TABLE IF NOT EXISTS SCHEMACHANGE.CHANGE_HISTORY
(
    VERSION        VARCHAR,
    DESCRIPTION    VARCHAR,
    SCRIPT         VARCHAR,
    SCRIPT_TYPE    VARCHAR,
    CHECKSUM       VARCHAR,
    EXECUTION_TIME NUMBER,
    STATUS         VARCHAR,
    INSTALLED_BY   VARCHAR,
    INSTALLED_ON   TIMESTAMP_LTZ
)
```

## Authentication

Schemachange supports the many of the authentication methods supported by
the [Snowflake Python Connector](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect).
The authenticator can be set by setting an `authenticator` in the [connections.toml](#connectionstoml-file) file

The following authenticators are supported:

- `snowflake`: [Password or PAT](#password-authentication)
- `oauth`: [External OAuth](#external-oauth-authentication)
- `externalbrowser`: [Browser-based SSO](#external-browser-authentication)
- `https://<okta_account_name>.okta.com`: [Okta SSO](#okta-authentication)
- `snowflake_jwt`: [Private Key](#private-key-authentication)

If an authenticator is unsupported, an exception will be raised.

### Password Authentication

Password authentication is the default authenticator. Supplying `snowflake` as your authenticator will set it
explicitly. A `password` may be supplied in the [connections.toml](#connectionstoml-file) file but can also
passed via environment variable `SNOWFLAKE_PASSWORD` (recommended).

The password parameter also accepts the Programmatic Access Token as long as the value for password is the PAT value.

### External OAuth Authentication

External OAuth authentication can be selected by supplying `oauth` as your authenticator. A `token_file_path` must be
supplied in the [connections.toml](#connectionstoml-file) file

**Schemachange no longer supports the `--oauth-config` option.**  Prior to the 4.0 release, this library supported
supplying an `--oauth-config` that would be used to fetch an OAuth token via the `requests` library. This required
Schemachange to keep track of connection arguments that could otherwise be passed directly to the Snowflake Python
connector. Maintaining this logic in Schemachange added unnecessary complication to the repo and prevented access to
recent connector parameterization features offered by the Snowflake connector.

### External Browser Authentication

External browser authentication can be selected by supplying `externalbrowser` as your authenticator. The client will be
prompted to authenticate in a browser that pops up. Refer to
the [documentation](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth-use.html#setting-up-browser-based-sso)
to cache the token to minimize the number of times the browser pops up to authenticate the user.

### Okta Authentication

External browser authentication can be selected by supplying your Okta endpoint as your authenticator (e.g.
`https://<org_name>.okta.com`). For clients that do not have a browser, can use the popular SaaS Idp option to connect
via Okta. A `password` must be supplied in the [connections.toml](#connectionstoml-file) file

_** NOTE**: Please disable Okta MFA for the user who uses Native SSO authentication with client drivers. Please consult
your Okta administrator for more information._

### Private Key Authentication

Private key authentication can be selected by supplying `snowflake_jwt` as your authenticator. The filepath to a
Snowflake user-encrypted private key must be supplied as `private_key_file` in the [connections.toml](#connectionstoml-file)
file. If the private key file is password protected, supply the password as `private_key_file_pwd` in
the [connections.toml](#connectionstoml-file) file. If the variable is not set, the Snowflake Python connector will
assume the private key is not encrypted.

## Configuration

schemachange supports multiple configuration methods for both Snowflake connection parameters and schemachange-specific settings. Configuration can be supplied through (in order of priority):

1. **Command Line Arguments** - Explicit flags passed to the CLI
2. **Environment Variables** - `SNOWFLAKE_*` prefixed variables (as of v4.1.0)
3. **YAML Config File** - `schemachange-config.yml` configuration file
4. **connections.toml File** - Snowflake Python Connector's connection file (as of v4.0)

Higher priority sources override lower priority sources, allowing flexible configuration management across different environments.

**Note:** As of 4.0, `vars` provided via command-line argument will be merged with vars provided via YAML config.
Previously, one overwrote the other completely.

Please see [Usage Notes for the account Parameter (for the connect Method)](https://docs.snowflake.com/en/user-guide/python-connector-api.html#label-account-format-info) for more details on how to structure the account name.

### connections.toml File

A [connections.toml](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect#connecting-using-the-connections-toml-file) file is used by the Snowflake Python Connector to store connection parameters. schemachange supports loading connection configurations from this file.

The `connections.toml` filepath can be supplied in the following ways (in order of priority):

1. The `--connections-file-path` [command-line argument](#commands)
2. The `SNOWFLAKE_CONNECTIONS_FILE_PATH` [environment variable](#environment-variables)
3. The `connections-file-path` [YAML value](#yaml-config-file)
4. Default location determined by the Snowflake Python Connector (typically `~/.snowflake/connections.toml`, or `$SNOWFLAKE_HOME/connections.toml` if `SNOWFLAKE_HOME` is set)

A connection profile name can be supplied in the following ways (in order of priority):

1. The `--connection-name` [command-line argument](#commands)
2. The `SNOWFLAKE_DEFAULT_CONNECTION_NAME` [environment variable](#environment-variables)
3. The `connection-name` [YAML value](#yaml-config-file)
4. Default: `default` (the Snowflake Python Connector uses the `[default]` profile if no name is specified)

### YAML Config File

By default, Schemachange expects the YAML config file to be named `schemachange-config.yml`, located in the current
working directory. The YAML file name can be overridden with the
`--config-file-name` [command-line argument](#commands). The folder can be overridden by using the
`--config-folder` [command-line argument](#commands)

schemachange supports two YAML configuration formats:

#### Config Version 2 (Recommended)

Config version 2 separates schemachange-specific parameters from Snowflake connector parameters into distinct sections, providing better organization and clarity:

```yaml
config-version: 2

schemachange:
  # The root folder for the database change scripts
  root-folder: './migrations'

  # The modules folder for jinja macros and templates to be used across multiple scripts
  modules-folder: './modules'

  # Override the default connections.toml file path
  connections-file-path: '~/.snowflake/connections.toml'

  # Override the default connections.toml connection name
  connection-name: 'my-connection'

  # Used to override the default name of the change history table (default: METADATA.SCHEMACHANGE.CHANGE_HISTORY)
  change-history-table: 'METADATA.SCHEMACHANGE.CHANGE_HISTORY'

  # Define values for variables to be replaced in change scripts
  vars:
    var1: 'value1'
    var2: 'value2'
    secrets:
      var3: 'value3' # This is considered a secret and will not be displayed in any output

  # Create the change history schema and table if they do not exist (default: false)
  create-change-history-table: true

  # Enable autocommit feature for DML commands (default: false)
  autocommit: false

  # Run schemachange in dry run mode (default: false)
  dry-run: false

  # A string to include in the QUERY_TAG that is attached to every SQL statement
  query-tag: 'my-project'

  # Log level: DEBUG, INFO, WARNING, ERROR, or CRITICAL (default: INFO)
  log-level: 'INFO'

  # Regex pattern for version number validation
  version-number-validation-regex: '^[0-9]+\.[0-9]+\.[0-9]+$'

  # Raise exception when versioned scripts are ignored (default: false)
  raise-exception-on-ignored-versioned-script: false

snowflake:
  # Snowflake connection parameters (these can also come from connections.toml or environment variables)
  account: 'myaccount.us-east-1'
  user: 'my_user'
  role: 'MY_ROLE'
  warehouse: 'MY_WH'
  database: 'MY_DB'
  schema: 'MY_SCHEMA'

  # Authentication parameters (optional, based on auth method)
  authenticator: 'snowflake_jwt'  # snowflake, oauth, externalbrowser, snowflake_jwt, or okta URL
  private-key-path: '~/.ssh/snowflake_key.p8'

  # Additional Snowflake Python Connector parameters
  # Any valid connector parameter can be specified here
  client-session-keep-alive: true
  login-timeout: 60
  network-timeout: 120
```

**Benefits of Config Version 2:**
- Clear separation between schemachange config and Snowflake connector parameters
- All Snowflake Python Connector parameters are supported in the `snowflake` section
- Better organization and maintainability
- Forward-compatible with future schemachange releases

#### Config Version 1 (Legacy, Backward Compatible)

Config version 1 uses a flat structure. This format is still supported for backward compatibility:

```yaml
config-version: 1

# The root folder for the database change scripts
root-folder: '/path/to/folder'

# The modules folder for jinja macros and templates to be used across multiple scripts.
modules-folder: null

# Override the default connections.toml file path at snowflake.connector.constants.CONNECTIONS_FILE (OS specific)
connections-file-path: null

# Override the default connections.toml connection name. Other connection-related values will override these connection values.
connection-name: null

# Used to override the default name of the change history table (the default is METADATA.SCHEMACHANGE.CHANGE_HISTORY)
change-history-table: null

# Define values for the variables to replaced in change scripts. vars supplied via the command line will be merged into YAML-supplied vars
vars:
  var1: 'value1'
  var2: 'value2'
  secrets:
    var3: 'value3' # This is considered a secret and will not be displayed in any output

# Create the change history schema and table, if they do not exist (the default is False)
create-change-history-table: false

# Enable autocommit feature for DML commands (the default is False)
autocommit: false

# Display verbose debugging details during execution (the default is False)
verbose: false

# Run schemachange in dry run mode (the default is False)
dry-run: false

# A string to include in the QUERY_TAG that is attached to every SQL statement executed
query-tag: 'QUERY_TAG'
```

**Note:** If `config-version` is not specified, schemachange assumes version 1 for backward compatibility.

#### Yaml Jinja support

The YAML config file supports the jinja templating language and has a custom function "env_var" to access environmental
variables. Jinja variables are unavailable and not yet loaded since they are supplied by the YAML file. Customisation of
the YAML file can only happen through values passed via environment variables.

##### env_var

Provides access to environmental variables. The function can be used two different ways.

Return the value of the environmental variable if it exists, otherwise return the default value.

```jinja
{{ env_var('<environmental_variable>', 'default') }}
```

Return the value of the environmental variable if it exists, otherwise raise an error.

```jinja
{{ env_var('<environmental_variable>') }}
```

### Environment Variables

schemachange supports two types of environment variables for configuration:

1. **`SCHEMACHANGE_*`** - For schemachange-specific settings (e.g., `SCHEMACHANGE_ROOT_FOLDER`)
2. **`SNOWFLAKE_*`** - For Snowflake connection and connector parameters (e.g., `SNOWFLAKE_ACCOUNT`)

Environment variables follow the naming convention where the prefix (`SCHEMACHANGE_` or `SNOWFLAKE_`) is followed by the parameter name in UPPERCASE with underscores replacing hyphens.

#### SCHEMACHANGE_* Environment Variables

These environment variables configure schemachange-specific behavior:

| Environment Variable | Description | Example | Type |
|---------------------|-------------|---------|------|
| `SCHEMACHANGE_ROOT_FOLDER` | The root folder for database change scripts | `./migrations` | string |
| `SCHEMACHANGE_MODULES_FOLDER` | The modules folder for jinja macros and templates | `./modules` | string |
| `SCHEMACHANGE_CHANGE_HISTORY_TABLE` | Override the default change history table name | `METADATA.SCHEMACHANGE.CHANGE_HISTORY` | string |
| `SCHEMACHANGE_VARS` | Define variables for scripts in JSON format | `{"var1": "value1", "var2": "value2"}` | JSON |
| `SCHEMACHANGE_CREATE_CHANGE_HISTORY_TABLE` | Create change history table if it doesn't exist | `true` or `false` | boolean |
| `SCHEMACHANGE_AUTOCOMMIT` | Enable autocommit for DML commands | `true` or `false` | boolean |
| `SCHEMACHANGE_DRY_RUN` | Run in dry run mode | `true` or `false` | boolean |
| `SCHEMACHANGE_QUERY_TAG` | String to include in QUERY_TAG for SQL statements | `my-project` | string |
| `SCHEMACHANGE_LOG_LEVEL` | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` | string |
| `SCHEMACHANGE_CONNECTIONS_FILE_PATH` | Path to connections.toml file | `~/.snowflake/connections.toml` | string |
| `SCHEMACHANGE_CONNECTION_NAME` | Connection profile name from connections.toml | `production` | string |

**Note:** Boolean values accept `true`/`false`, `yes`/`no`, `1`/`0` (case-insensitive).

#### SNOWFLAKE_* Environment Variables

##### Explicit Connection Parameters

These Snowflake-specific environment variables are explicitly handled by schemachange:

| Environment Variable | Description | Example |
|---------------------|-------------|---------|
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier | `myaccount.us-east-1` |
| `SNOWFLAKE_USER` | Username for authentication | `my_user` |
| `SNOWFLAKE_PASSWORD` | Password for authentication (also supports PATs) | `my_password` or `<pat_token>` |
| `SNOWFLAKE_ROLE` | Role to use after connecting | `TRANSFORMER` |
| `SNOWFLAKE_WAREHOUSE` | Default warehouse | `COMPUTE_WH` |
| `SNOWFLAKE_DATABASE` | Default database | `MY_DATABASE` |
| `SNOWFLAKE_SCHEMA` | Default schema | `PUBLIC` |

##### Authentication Parameters

| Environment Variable | Description | Example |
|---------------------|-------------|---------|
| `SNOWFLAKE_AUTHENTICATOR` | Authentication method | `snowflake`, `oauth`, `externalbrowser`, `snowflake_jwt`, or `https://<okta_account>.okta.com` |
| `SNOWFLAKE_PRIVATE_KEY_PATH` | Path to private key file for JWT authentication | `~/.ssh/snowflake_key.p8` |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | Passphrase for encrypted private key | `my_key_password` |
| `SNOWFLAKE_TOKEN_FILE_PATH` | Path to OAuth token file (for external OAuth only) | `~/.snowflake/oauth_token.txt` |

##### Generic SNOWFLAKE_* Parameters (Pass-through)

**NEW:** Any `SNOWFLAKE_*` environment variable not explicitly listed above will be automatically passed through to the Snowflake Python Connector. This allows you to use any connector parameter via environment variables.

Common pass-through parameters include:

| Environment Variable | Description | Example |
|---------------------|-------------|---------|
| `SNOWFLAKE_CLIENT_SESSION_KEEP_ALIVE` | Keep the session alive | `true` or `false` |
| `SNOWFLAKE_LOGIN_TIMEOUT` | Login timeout in seconds | `60` |
| `SNOWFLAKE_NETWORK_TIMEOUT` | Network timeout in seconds | `120` |
| `SNOWFLAKE_CLIENT_PREFETCH_THREADS` | Number of threads for result prefetching | `4` |
| `SNOWFLAKE_CLIENT_STORE_TEMPORARY_CREDENTIAL` | Store temporary credentials | `true` or `false` |

For a complete list of supported connector parameters, see the [Snowflake Python Connector documentation](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect).

**Note on PATs (Programmatic Access Tokens):** For CI/CD pipelines and service accounts, especially with Snowflake's MFA enforcement, use PATs via `SNOWFLAKE_PASSWORD`. PATs use the default `snowflake` authenticator—no need to set `SNOWFLAKE_AUTHENTICATOR`. The Snowflake connector automatically detects PAT tokens.

#### Configuration File Parameters

| Environment Variable | Description | Example |
|---------------------|-------------|---------|
| `SNOWFLAKE_CONNECTIONS_FILE_PATH` | Custom path to `connections.toml` file | `/custom/path/connections.toml` |
| `SNOWFLAKE_HOME` | Custom Snowflake home directory (default: `~/.snowflake`) | `~/.snowflake` |
| `SNOWFLAKE_DEFAULT_CONNECTION_NAME` | Default connection profile name from `connections.toml` | `production` |

#### Legacy Environment Variables

| Environment Variable | Description | Status |
|---------------------|-------------|--------|
| `SNOWSQL_PWD` | Legacy password variable | **Deprecated** - Use `SNOWFLAKE_PASSWORD` instead |

#### Example Usage

**Basic Password Authentication:**
```bash
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="deploy_user"
export SNOWFLAKE_PASSWORD="secure_password"
export SNOWFLAKE_ROLE="DEPLOY_ROLE"
export SNOWFLAKE_WAREHOUSE="DEPLOY_WH"
export SNOWFLAKE_DATABASE="MY_DATABASE"

schemachange deploy --config-folder ./migrations
```

**Key-Pair Authentication:**
```bash
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="deploy_user"
export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
export SNOWFLAKE_PRIVATE_KEY_PATH="~/.ssh/snowflake_key.p8"
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE="key_password"
export SNOWFLAKE_ROLE="DEPLOY_ROLE"

schemachange deploy --config-folder ./migrations
```

**Programmatic Access Token (PAT):**
```bash
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="service_account"
export SNOWFLAKE_PASSWORD="<your_pat_token>"
export SNOWFLAKE_ROLE="DEPLOY_ROLE"

schemachange deploy --config-folder ./migrations
```

### Configuration Priority

schemachange uses a layered configuration approach with the following priority order (highest to lowest):

1. **Command Line Arguments** - Explicitly provided CLI flags (e.g., `--snowflake-account`)
2. **Environment Variables** - `SNOWFLAKE_*` prefixed variables
3. **YAML Configuration File** - Settings in `schemachange-config.yml`
4. **connections.toml File** - Snowflake Python Connector's connection file

This means:
- CLI arguments override everything
- Environment variables override YAML and connections.toml
- YAML configuration overrides connections.toml
- connections.toml provides base defaults

**Example Priority Resolution:**

If you have:
- `connections.toml` with `user = "toml_user"`
- YAML with `snowflake-user: yaml_user`
- Environment variable `SNOWFLAKE_USER=env_user`
- CLI argument `--snowflake-user cli_user`

The effective user will be `cli_user` (CLI wins).

This priority system allows you to:
- Set base configuration in `connections.toml`
- Override per-environment in YAML files
- Override for CI/CD with environment variables
- Override for specific runs with CLI arguments

**Snowflake Python Connector Parameters:**

schemachange now provides multiple ways to pass parameters to the Snowflake Python Connector:

1. **Explicit Parameters** - Common connection parameters (`account`, `user`, `role`, `warehouse`, `database`, `schema`) can be specified via:
   - CLI arguments (e.g., `--snowflake-account`, `-a`)
   - Environment variables (e.g., `SNOWFLAKE_ACCOUNT`)
   - YAML configuration (v1 or v2)
   - connections.toml file

2. **Additional Connector Parameters** - Any Snowflake connector parameter can be specified via:
   - **Config Version 2 YAML:** Use the `snowflake:` section to specify any connector parameter
   - **Generic `SNOWFLAKE_*` Environment Variables:** Any `SNOWFLAKE_*` variable not explicitly handled will be passed through to the connector
   - **connections.toml file:** Full parameter set support

**Example: Using Additional Connector Parameters**

```yaml
# Config Version 2 YAML (Recommended)
config-version: 2

snowflake:
  account: 'myaccount.us-east-1'
  user: 'my_user'
  # Additional connector parameters
  client-session-keep-alive: true
  login-timeout: 60
  network-timeout: 120
```

```bash
# Environment Variables
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_CLIENT_SESSION_KEEP_ALIVE="true"
export SNOWFLAKE_LOGIN_TIMEOUT="60"
export SNOWFLAKE_NETWORK_TIMEOUT="120"

schemachange deploy
```

For comprehensive connector documentation and the full list of connection parameters, see the [Snowflake Python Connector documentation](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect).

## Commands

Schemachange supports a few subcommands. If the subcommand is not provided it defaults to deploy. This behaviour keeps
compatibility with versions prior to 3.2.

### deploy

This is the main command that runs the deployment process.

#### Command-Line Arguments

schemachange supports prefixed CLI arguments for better clarity and organization:
- `--schemachange-*` for schemachange-specific parameters
- `--snowflake-*` for Snowflake connection parameters

Most arguments also support short forms (single dash, single letter) for convenience.

**General Configuration**

| Parameter | Short Form | Description |
|-----------|------------|-------------|
| -h, --help | | Show the help message and exit |
| --config-folder CONFIG_FOLDER | | The folder to look in for the schemachange config file (default: current working directory) |
| --config-file-name CONFIG_FILE_NAME | | The file name of the schemachange config file (default: schemachange-config.yml) |

**Schemachange Parameters**

| Parameter | Short Form | Environment Variable | Description |
|-----------|------------|---------------------|-------------|
| -f, --schemachange-root-folder, --root-folder | -f | SCHEMACHANGE_ROOT_FOLDER | The root folder for database change scripts (default: current directory). Deprecated alias: --root-folder |
| -m, --schemachange-modules-folder, --modules-folder | -m | SCHEMACHANGE_MODULES_FOLDER | The modules folder for jinja macros and templates. Deprecated alias: --modules-folder |
| -c, --schemachange-change-history-table, --change-history-table | -c | SCHEMACHANGE_CHANGE_HISTORY_TABLE | Override the default change history table name (default: METADATA.SCHEMACHANGE.CHANGE_HISTORY). Deprecated alias: --change-history-table |
| -V, --schemachange-vars, --vars | -V | SCHEMACHANGE_VARS | Define variables for scripts in JSON format. Merged with YAML vars (e.g., '{"var1": "val1"}'). Deprecated alias: --vars |
| --schemachange-create-change-history-table, --create-change-history-table | | SCHEMACHANGE_CREATE_CHANGE_HISTORY_TABLE | Create the change history table if it doesn't exist (default: false). Deprecated alias: --create-change-history-table |
| -ac, --schemachange-autocommit, --autocommit | -ac | SCHEMACHANGE_AUTOCOMMIT | Enable autocommit for DML commands (default: false). Deprecated alias: --autocommit |
| --schemachange-dry-run, --dry-run | | SCHEMACHANGE_DRY_RUN | Run in dry run mode (default: false). Deprecated alias: --dry-run |
| -Q, --schemachange-query-tag, --query-tag | -Q | SCHEMACHANGE_QUERY_TAG | String to include in QUERY_TAG attached to every SQL statement. Deprecated alias: --query-tag |
| -L, --schemachange-log-level, --log-level | -L | SCHEMACHANGE_LOG_LEVEL | Logging level: DEBUG, INFO, WARNING, ERROR, or CRITICAL (default: INFO). Deprecated alias: --log-level |
| -C, --schemachange-connection-name, --connection-name | -C | SCHEMACHANGE_CONNECTION_NAME | Override the default connections.toml connection profile name. Deprecated alias: --connection-name |
| --schemachange-connections-file-path, --connections-file-path | | SCHEMACHANGE_CONNECTIONS_FILE_PATH | Override the default connections.toml file path. Deprecated alias: --connections-file-path |
| -v, --verbose | -v | | Display verbose debugging details (deprecated, use -L DEBUG or --schemachange-log-level DEBUG instead) |

**Snowflake Connection Parameters**

| Parameter | Short Form | Environment Variable | Description |
|-----------|------------|---------------------|-------------|
| -a, --snowflake-account | -a | SNOWFLAKE_ACCOUNT | Snowflake account identifier (e.g., myaccount.us-east-1) |
| -u, --snowflake-user | -u | SNOWFLAKE_USER | Username for authentication |
| -r, --snowflake-role | -r | SNOWFLAKE_ROLE | Role to use after connecting |
| -w, --snowflake-warehouse | -w | SNOWFLAKE_WAREHOUSE | Default warehouse |
| -d, --snowflake-database | -d | SNOWFLAKE_DATABASE | Default database |
| -s, --snowflake-schema | -s | SNOWFLAKE_SCHEMA | Default schema |
| --snowflake-authenticator | | SNOWFLAKE_AUTHENTICATOR | Authentication method (e.g., 'snowflake', 'oauth', 'externalbrowser', 'snowflake_jwt') |
| --snowflake-private-key-path | | SNOWFLAKE_PRIVATE_KEY_PATH | Path to private key file for JWT authentication |
| --snowflake-private-key-passphrase | | SNOWFLAKE_PRIVATE_KEY_PASSPHRASE | Passphrase for encrypted private key |
| --snowflake-token-file-path | | SNOWFLAKE_TOKEN_FILE_PATH | Path to OAuth token file (use with --snowflake-authenticator oauth) |

**Note on Argument Aliases:**
- Multiple argument forms are supported for backward compatibility (e.g., `-f`, `--schemachange-root-folder`, `--root-folder`)
- The recommended forms are the short forms (e.g., `-f`, `-m`, `-c`) or the explicit prefixed forms (e.g., `--schemachange-root-folder`)
- Deprecated aliases (e.g., `--root-folder`, `--vars`, `--query-tag`) are noted in the help text but continue to work
- All variants of an argument set the same configuration value
- Use the prefixed forms (`--schemachange-*`, `--snowflake-*`) or short forms for clarity and future compatibility

### render

This subcommand is used to render a single script to the console. It is intended to support the development and
troubleshooting of script that use features from the jinja template engine.

`usage: schemachange render [-h] [--config-folder CONFIG_FOLDER] [-f ROOT_FOLDER] [-m MODULES_FOLDER] [-V VARS] [-L LOG_LEVEL] script`

| Parameter | Description |
|-----------|-------------|
| --config-folder, --schemachange-config-folder | The folder to look in for the schemachange-config.yml file (the default is the current working directory) |
| -f, --schemachange-root-folder, --root-folder | The root folder for the database change scripts |
| -m, --schemachange-modules-folder, --modules-folder | The modules folder for jinja macros and templates to be used across multiple scripts |
| -V, --schemachange-vars, --vars | Define values for the variables to replaced in change scripts, given in JSON format (e.g. {"variable1": "value1", "variable2": "value2"}) |
| -L, --schemachange-log-level, --log-level | Logging level: DEBUG, INFO, WARNING, ERROR, or CRITICAL (default: INFO) |
| script | Path to the script to render |

## Running schemachange

### Prerequisites

In order to run schemachange you must have the following:

* You will need to have a recent version of python 3 installed
* You will need to have the
  latest [Snowflake Python driver installed](https://docs.snowflake.com/en/user-guide/python-connector-install.html)
* You will need to create the change history table used by schemachange in Snowflake (
  see [Change History Table](#change-history-table) above for more details)
    * First, you will need to create a database to store your change history table (schemachange will not help you with
      this). For your convenience, [initialize.sql file](demo/provision/initialize.sql) has been provided to get you
      started. Feel free to align the script to your organizations RBAC implementation.
      The [setup_schemachange_schema.sql](demo/provision/setup_schemachange_schema.sql) file is provided to set up the
      target schema that will host the change history table for each of the demo projects in this repo. Use it as a
      means to test the required permissions and connectivity in your local setup.
    * Second, you will need to create the change history schema and table. You can do this manually (
      see [Change History Table](#change-history-table) above for the DDL) or have schemachange create them by running
      it with the `--create-change-history-table` parameter (just make sure the Snowflake user you're running
      schemachange with has privileges to create a schema and table in that database)
* You will need to create (or choose) a user account that has privileges to apply the changes in your change script
    * Don't forget that this user also needs the SELECT and INSERT privileges on the change history table

### Running the Script

schemachange is a single python script located at [schemachange/cli.py](schemachange/cli.py). It can be executed as
follows:

```bash
python schemachange/cli.py [-h] [--config-folder CONFIG_FOLDER] [-f ROOT_FOLDER] [-c CHANGE_HISTORY_TABLE] [-V VARS] [--create-change-history-table] [-ac] [-L LOG_LEVEL] [--dry-run] [-Q QUERY_TAG] [--connections-file-path CONNECTIONS_FILE_PATH] [-C CONNECTION_NAME]
```

Or if installed via `pip`, it can be executed as follows:

```bash
schemachange deploy [-h] [--config-folder CONFIG_FOLDER] [-f ROOT_FOLDER] [-c CHANGE_HISTORY_TABLE] [-V VARS] [--create-change-history-table] [-ac] [-L LOG_LEVEL] [--dry-run] [-Q QUERY_TAG] [--connections-file-path CONNECTIONS_FILE_PATH] [-C CONNECTION_NAME]
```

**Note:** All arguments support multiple forms for backward compatibility. See the [deploy command](#deploy) section for the full list of argument variants.

The [demo](demo) folder in this project repository contains three schemachange demo projects for you to try out. These
demos showcase the basics and a couple of advanced examples based on the standard Snowflake Citibike demo which can be
found in [the Snowflake Hands-on Lab](https://docs.snowflake.net/manuals/other-resources.html#hands-on-lab). Check out
each demo listed below

- [Basics Demo](demo/basics_demo): Used to test the basic schemachange functionality.
- [Citibike Demo](demo/citibike_demo): Used to show a simple example of building a database and loading data using
  schemachange.
- [Citibike Jinja Demo](demo/citibike_demo_jinja): Extends the citibike demo to showcase the use of macros and jinja
  templating.

The [Citibike data](https://www.citibikenyc.com/system-data) for this demo comes from the NYC Citi Bike bike share
program.

To get started with schemachange and these demo scripts follow these steps:

1. Make sure you've completed the [Prerequisites](#prerequisites) steps above
1. Get a copy of this schemachange repository (either via a clone or download)
1. Open a shell and change directory to your copy of the schemachange repository
1. Run schemachange (see [Running the Script](#running-the-script) above) with your Snowflake account details and
   respective demo project as the root folder (make sure you use the full path)

## Integrating With DevOps

### Sample DevOps Process Flow

Here is a sample DevOps development lifecycle with schemachange:

<img src="https://github.com/user-attachments/assets/42eae968-ae76-4fcb-a0ba-3995ec977818" alt="schemachange DevOps process" title="schemachange DevOps process" />

### Using in a CI/CD Pipeline

If your build agent has a recent version of python 3 installed, the script can be run like so:

```bash
pip install schemachange --upgrade
schemachange deploy [-f ROOT_FOLDER] [-c CHANGE_HISTORY_TABLE] [-V VARS] [--create-change-history-table] [-ac] [-L LOG_LEVEL] [--dry-run] [-Q QUERY_TAG] [--connections-file-path CONNECTIONS_FILE_PATH] [-C CONNECTION_NAME]
```

Or if you prefer docker, run like so:

```bash
docker run -it --rm \
  --name schemachange-script \
  -v "$PWD":/usr/src/schemachange \
  -w /usr/src/schemachange \
  -e ROOT_FOLDER \
  -e $CONNECTION_NAME \
  python:3 /bin/bash -c "pip install schemachange --upgrade && schemachange -f $ROOT_FOLDER --connections-file-path connections.toml --connection-name $CONNECTION_NAME"
```

Either way, don't forget to configure a [connections.toml file](#connectionstoml-file) for connection parameters

## Maintainers

- James Weakley (@jamesweakley)
- Jeremiah Hansen (@jeremiahhansen)

This is a community-developed tool, not an official Snowflake offering. It comes with no support or warranty. However,
feel free to raise a GitHub issue if you find a bug or would like a new feature.

## Third Party Packages

The current functionality in schemachange would not be possible without the following third party packages and all those
that maintain and have contributed.

| Name                       | License                 | Author                                                                                                           | URL                                  |
|----------------------------|-------------------------|------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| Jinja2                     | BSD License             | Armin Ronacher                                                                                                   | https://palletsprojects.com/p/jinja/ |
| PyYAML                     | MIT License             | Kirill Simonov                                                                                                   | https://pyyaml.org/                  |
| pandas                     | BSD License             | The Pandas Development Team                                                                                      | https://pandas.pydata.org            |
| pytest                     | MIT License             | Holger Krekel, Bruno Oliveira, Ronny Pfannschmidt, Floris Bruynooghe, Brianna Laugher, Florian Bruhin and others | https://docs.pytest.org/en/latest/   |
| snowflake-connector-python | Apache Software License | Snowflake, Inc                                                                                                   | https://www.snowflake.com/           |

## Legal

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this tool except in compliance with the
License. You may obtain a copy of the License
at: [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "
AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.
