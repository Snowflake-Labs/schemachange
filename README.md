# schemachange

<img src="images/schemachange-logo-title.png" alt="schemachange" title="schemachange logo" width="600" />

*Looking for snowchange? You've found the right spot. snowchange has been renamed to schemachange.*

[![pytest](https://github.com/Snowflake-Labs/schemachange/actions/workflows/master-pytest.yml/badge.svg)](https://github.com/Snowflake-Labs/schemachange/actions/workflows/master-pytest.yml)
[![PyPI](https://img.shields.io/pypi/v/schemachange.svg)](https://pypi.org/project/schemachange)

## Overview

schemachange is a simple python based tool to manage all of your [Snowflake](https://www.snowflake.com/) objects. It
follows an Imperative-style approach to Database Change Management (DCM) and was inspired by
the [Flyway database migration tool](https://flywaydb.org). When combined with a version control system and a CI/CD
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
    1. [Environment Variables](#environment-variables)
    1. [YAML Config File](#yaml-config-file)
        1. [Yaml Jinja support](#yaml-jinja-support)
    1. [connections.toml File](#connectionstoml-file)
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

The schemachange folder structure is very flexible. The `project_root` folder is specified with the `-f`
or `--root-folder` argument. schemachange only pays attention to the filenames, not the paths. Therefore, under
the `project_root` folder you are free to arrange the change scripts any way you see fit. You can have as many
subfolders (and nested subfolders) as you would like.

## Change Scripts

### Versioned Script Naming

Versioned change scripts follow a similar naming convention to that used
by [Flyway Versioned Migrations](https://flywaydb.org/documentation/migrations#versioned-migrations). The script name
must follow this pattern (image taken
from [Flyway docs](https://flywaydb.org/documentation/migrations#versioned-migrations)):

<img src="images/flyway-naming-convention.png" alt="Flyway naming conventions" title="Flyway naming conventions" width="300" />

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
accidently (re-)use the same version number.

### Repeatable Script Naming

Repeatable change scripts follow a similar naming convention to that used
by [Flyway Versioned Migrations](https://flywaydb.org/documentation/concepts/migrations.html#repeatable-migrations). The
script name must follow this pattern (image taken
from [Flyway docs](https://flywaydb.org/documentation/concepts/migrations.html#repeatable-migrations):

<img src="images/flyway-repeatable-naming-convention.png" alt="Flyway naming conventions" title="Flyway naming conventions" width="300" />

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
of [Flyway Versioned Migrations](https://flywaydb.org/documentation/concepts/migrations.html#repeatable-migrations).
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
the target Snowflake account, in the correct order.

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

The Jinja autoescaping feature is disabled in schemachange, this feature in Jinja is currently designed for where the
output language is HTML/XML. So if you are using schemachange with untrusted inputs you will need to handle this within
your change scripts.

### Gotchas

Within change scripts:

- [Snowflake Scripting blocks need delimiters](https://docs.snowflake.com/en/developer-guide/snowflake-scripting/running-examples#introduction)
- [The last line can't be a comment](https://github.com/Snowflake-Labs/schemachange/issues/130)

## Change History Table

schemachange records all applied changes scripts to the change history table. By default, schemachange will attempt to
log all activities to the `METADATA.SCHEMACHANGE.CHANGE_HISTORY` table. The name and location of the change history
table can be overriden via a command line argument (`-c` or `--change-history-table`) or the `schemachange-config.yml`
file ( `change-history-table`). The value passed to the parameter can have a one, two, or three part name (e.g. "
TABLE_NAME", or "SCHEMA_NAME.TABLE_NAME", or " DATABASE_NAME.SCHEMA_NAME.TABLE_NAME"). This can be used to support
multiple environments (dev, test, prod) or multiple subject areas within the same Snowflake account.

By default, schemachange will not try to create the change history table, and it will fail if the table does not exist.
This behavior can be altered by passing in the `--create-change-history-table` argument or adding
`create-change-history-table: true` to the `schemachange-config.yml` file. Even with the `--create-change-history-table`
parameter, schemachange will not attempt to create the database for the change history table. That must be created
before running schemachange.

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
In order of priority, the authenticator can be set with:

1. The `SNOWFLAKE_AUTHENTICATOR` [environment variable](#environment-variables)
2. The `--snowflake-authenticator` [command-line argument](#commands)
3. Setting a `snowflake-authenticator` in the [schemachange-config.yml](#yaml-config-file) file
4. Setting an `authenticator` in the [connections.toml](#connectionstoml-file) file

The following authenticators are supported:

- `snowflake`: [Password](#password-authentication)
- `oauth`: [External OAuth](#external-oauth-authentication)
- `externalbrowser`: [Browser-based SSO](#external-browser-authentication)
- `https://<okta_account_name>.okta.com`: [Okta SSO](#okta-authentication)
- `snowflake_jwt`: [Private Key](#private-key-authentication)

If an authenticator is unsupported, an exception will be raised.

### Password Authentication

Password authentication is the authenticator. Supplying `snowflake` as your authenticator will set it explicitly. A
password must be supplied in one of the following ways (in order of priority):

1. The `SNOWFLAKE_PASSWORD` [environment variable](#environment-variables)
2. The `SNOWSQL_PWD` [environment variable](#environment-variables). _**DEPRECATION NOTICE**: The `SNOWSQL_PWD`
   environment variable is deprecated but currently still supported. Support for
   it will be removed in a later version of schemachange. Please use `SNOWFLAKE_PASSWORD` instead._
3. Setting a `password` in the [connections.toml](#connectionstoml-file) file

### External OAuth Authentication

External OAuth authentication can be selected by supplying `oauth` as your authenticator. In order of preference, a
token will need to be supplied or acquired in one of the following ways:

1. Supply a token via the `SNOWFLAKE_TOKEN` [environment variable](#environment-variables)
2. Supply a token path in one of the following ways (in order of priority). The token path will be passed directly to
   the Snowflake connector.
    1. The `--snowflake-token-path` [command-line argument](#commands)
    2. Setting a `snowflake-token-path` in the [schemachange-config.yml](#yaml-config-file) file
    3. Setting a `token_file_path` in the [connections.toml](#connectionstoml-file) file
3. Supply an "OAuth config" in one of the following ways (in order of priority):

    1. The `--oauth-config` [command-line argument](#commands)
    2. Setting an `oauthconfig` in the [schemachange-config.yml](#yaml-config-file) file

   Since different Oauth providers may require different information the Oauth
   configuration uses four named variables that are fed into a POST request to obtain a token. Azure is shown in the
   example YAML but other providers should use a similar pattern and request payload contents.

    * token-provider-url
      The URL of the authenticator resource that will receive the POST request.
    * token-response-name
      The Expected name of the JSON element containing the Token in the return response from the authenticator resource.
    * token-request-payload
      The Set of variables passed as a dictionary to the `data` element of the request.
    * token-request-headers
      The Set of variables passed as a dictionary to the `headers` element of the request.

   It is recommended to use the YAML file and pass oauth secrets into the configuration using the templating engine
   instead of the command line option.

   The OAuth POST call will only be made if a token or token filepath isn't discovered.

### External Browser Authentication

External browser authentication can be selected by supplying `externalbrowser` as your authenticator. The client will be
prompted to authenticate in a browser that pops up. Refer to
the [documentation](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth-use.html#setting-up-browser-based-sso)
to cache the token to minimize the number of times the browser pops up to authenticate the user.

### Okta Authentication

External browser authentication can be selected by supplying your Okta endpoint as your authenticator (e.g.
`https://<org_name>.okta.com`). For clients that do not have a browser, can use the popular SaaS Idp option to connect
via Okta. A password must be supplied in one of the following ways (in order of priority):

1. The `SNOWFLAKE_PASSWORD` [environment variable](#environment-variables)
2. The `SNOWSQL_PWD` [environment variable](#environment-variables). _**DEPRECATION NOTICE**: The `SNOWSQL_PWD`
   environment variable is deprecated but currently still supported. Support for
   it will be removed in a later version of schemachange. Please use `SNOWFLAKE_PASSWORD` instead._
3. Setting a `password` in the [connections.toml](#connectionstoml-file) file

_** NOTE**: Please disable Okta MFA for the user who uses Native SSO authentication with client drivers. Please consult
your Okta administrator for more information._

### Private Key Authentication

External browser authentication can be selected by supplying `snowflake_jwt` as your authenticator. The filepath to a
Snowflake user-encrypted private key must be supplied in one of the following ways (in order of priority):

1. The `SNOWFLAKE_PRIVATE_KEY_PATH` [environment variable](#environment-variables)
2. The `--snowflake-private-key-path` [command-line argument](#commands)
3. Setting a `snowflake-private-key-path` in the [schemachange-config.yml](#yaml-config-file) file
4. Setting an `private-key` in the [connections.toml](#connectionstoml-file) file

Additionally, the password for the encrypted private key file is required to be set in the environment variable
`SNOWFLAKE_PRIVATE_KEY_PASSPHRASE`. If the variable is not set, schemachange will assume the private key is not
encrypted.

## Configuration

Parameters to schemachange can be supplied in four different ways (in order of priority):

1. Environment Variables
2. Command Line Arguments
3. YAML config file
4. connections.toml file

**Note:** `vars` provided via command-line argument will be merged with vars provided via YAML config.

Not all parameters can be supplied via every method.

Please
see [Usage Notes for the account Parameter (for the connect Method)](https://docs.snowflake.com/en/user-guide/python-connector-api.html#label-account-format-info)
for more details on how to structure the account name.

### Environment Variables

The Snowflake Python connector subscribes to many variables. Schemachange won't alter environment variables, but it will
consider the following variables to detect an incomplete configuration:

- SNOWFLAKE_PASSWORD
- _Deprecated_ SNOWSQL_PWD
- SNOWFLAKE_PRIVATE_KEY_PATH
- SNOWFLAKE_AUTHENTICATOR
- SNOWFLAKE_TOKEN
- SNOWFLAKE_DEFAULT_CONNECTION_NAME

### YAML Config File

By default, Schemachange expects the YAML config file to be named `schemachange-config.yml`, located in the current
working directory. The YAML file name can be overridden with the
`--config-file-name` [command-line argument](#commands). The folder can be overridden by using the
`--config-folder` [command-line argument](#commands)

Here is the list of available configurations in the `schemachange-config.yml` file:

```yaml
config-version: 1

# The root folder for the database change scripts
root-folder: '/path/to/folder'

# The modules folder for jinja macros and templates to be used across multiple scripts.
modules-folder: null

# The name of the snowflake account (e.g. xy12345.east-us-2.azure).
# You can also use the regionless format (e.g. myorgname-accountname)
# for privatelink accounts, suffix the account value with privatelink (e.g. <account>.privatelink)
snowflake-account: 'xy12345.east-us-2.azure'

# The name of the snowflake user
snowflake-user: 'user'

# The name of the default role to use. Can be overridden in the change scripts.
snowflake-role: 'role'

# The name of the default warehouse to use. Can be overridden in the change scripts.
snowflake-warehouse: 'warehouse'

# The name of the default database to use. Can be overridden in the change scripts.
snowflake-database: null

# The name of the default schema to use. Can be overridden in the change scripts.
snowflake-schema: null

# The Snowflake Authenticator to use. One of snowflake, oauth, externalbrowser, or https://<okta_account_name>.okta.com
snowflake-authenticator: null

# Path to file containing private key. 
snowflake-private-key-path: null

# Path to the file containing the OAuth token to be used when authenticating with Snowflake.
snowflake-token-path: null

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

# Information for Oauth token requests
oauth-config:
  # url Where token request are posted to
  token-provider-url: 'https://login.microsoftonline.com/{{ env_var('AZURE_ORG_GUID', 'default') }}/oauth2/v2.0/token'
  # name of Json entity returned by request
  token-response-name: 'access_token'
  # Headers needed for successful post or other security markings ( multiple labeled items permitted
  token-request-headers:
    Content-Type: "application/x-www-form-urlencoded"
    User-Agent: "python/schemachange"
  # Request Payload for Token (it is recommended pass
  token-request-payload:
    client_id: '{{ env_var('CLIENT_ID', 'default') }}'
    username: '{{ env_var('USER_ID', 'default') }}'
    password: '{{ env_var('USER_PASSWORD', 'default') }}'
    grant_type: 'password'
    scope: '{{ env_var('SESSION_SCOPE', 'default') }}'
```

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

### connections.toml File

A `[connections.toml](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect#connecting-using-the-connections-toml-file)
filepath can be supplied in the following ways (in order of priority):

1. The `--connections-file-path` [command-line argument](#commands)
2. The `connections-file-path` [YAML value](#yaml-config-file)

A connection name can be supplied in the following ways (in order of priority):

1. The `SNOWFLAKE_DEFAULT_CONNECTION_NAME` [environment variable](#environment-variables)
2. The `--connection-name` [command-line argument](#commands)
3. The `connection-name` [YAML value](#yaml-config-file)

Schemachange will consider these connection parameters after environment variables, command line arguments, and the YAML
configuration.

```txt
[example connection name]
account = "example account"
user = "example user"
role = "example role"
warehouse = "example warehouse"
database = "example database"
schema = "example schema"
authenticator = "example authenticator"
password = "example password"
host = "example host"
port = "example port"
region = "example region"
private-key = "example private-key"
token_file_path = "example token_file_path"
```

## Commands

Schemachange supports a few subcommands. If the subcommand is not provided it defaults to deploy. This behaviour keeps
compatibility with versions prior to 3.2.

### deploy

This is the main command that runs the deployment process.

```bash
usage: schemachange deploy [-h] [--config-folder CONFIG_FOLDER] [--config-file-name CONFIG_FILE_NAME] [-f ROOT_FOLDER] [-m MODULES_FOLDER] [-a SNOWFLAKE_ACCOUNT] [-u SNOWFLAKE_USER] [-r SNOWFLAKE_ROLE] [-w SNOWFLAKE_WAREHOUSE] [-d SNOWFLAKE_DATABASE] [-s SNOWFLAKE_SCHEMA] [--snowflake-authenticator SNOWFLAKE_AUTHENTICATOR] [--snowflake-private-key-path SNOWFLAKE_PRIVATE_KEY_PATH] [--snowflake-token-path SNOWFLAKE_TOKEN_PATH] [--connections-file-path CONNECTIONS_FILE_PATH] [--connection-name CONNECTION_NAME] [-c CHANGE_HISTORY_TABLE] [--vars VARS] [--create-change-history-table] [-ac] [-v] [--dry-run] [--query-tag QUERY_TAG]
```

| Parameter                                                                              | Description                                                                                                                                                                                                                                                         |
|----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| -h, --help                                                                             | Show the help message and exit                                                                                                                                                                                                                                      |
| --config-folder CONFIG_FOLDER                                                          | The folder to look in for the schemachange config file (the default is the current working directory)                                                                                                                                                               |
| --config-file-name CONFIG_FILE_NAME                                                    | The file name of the schemachange config file. (the default is schemachange-config.yml)                                                                                                                                                                             |
| -f ROOT_FOLDER, --root-folder ROOT_FOLDER                                              | The root folder for the database change scripts. The default is the current directory.                                                                                                                                                                              |
| -m MODULES_FOLDER, --modules-folder MODULES_FOLDER                                     | The modules folder for jinja macros and templates to be used across mutliple scripts                                                                                                                                                                                |
| -a SNOWFLAKE_ACCOUNT, --snowflake-account SNOWFLAKE_ACCOUNT                            | The name of the snowflake account (e.g. xy12345.east-us-2.azure).                                                                                                                                                                                                   |
| -u SNOWFLAKE_USER, --snowflake-user SNOWFLAKE_USER                                     | The name of the snowflake user                                                                                                                                                                                                                                      |
| -r SNOWFLAKE_ROLE, --snowflake-role SNOWFLAKE_ROLE                                     | The name of the role to use                                                                                                                                                                                                                                         |
| -w SNOWFLAKE_WAREHOUSE, --snowflake-warehouse SNOWFLAKE_WAREHOUSE                      | The name of the default warehouse to use. Can be overridden in the change scripts.                                                                                                                                                                                  |
| -d SNOWFLAKE_DATABASE, --snowflake-database SNOWFLAKE_DATABASE                         | The name of the default database to use. Can be overridden in the change scripts.                                                                                                                                                                                   |
| -s SNOWFLAKE_SCHEMA, --snowflake-schema SNOWFLAKE_SCHEMA                               | The name of the default schema to use. Can be overridden in the change scripts.                                                                                                                                                                                     |
| -A SNOWFLAKE_AUTHENTICATOR, --snowflake-authenticator SNOWFLAKE_AUTHENTICATOR          | The Snowflake Authenticator to use. One of snowflake, oauth, externalbrowser, or https://<okta_account_name>.okta.com                                                                                                                                               |
| -k SNOWFLAKE_PRIVATE_KEY_PATH, --snowflake-private-key-path SNOWFLAKE_PRIVATE_KEY_PATH | Path to file containing private key.                                                                                                                                                                                                                                |
| -t SNOWFLAKE_TOKEN_PATH, --snowflake-token-path SNOWFLAKE_TOKEN_PATH                   | Path to the file containing the OAuth token to be used when authenticating with Snowflake.                                                                                                                                                                          |
| --connections-file-path CONNECTIONS_FILE_PATH                                          | Override the default [connections.toml](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect#connecting-using-the-connections-toml-file) file path at snowflake.connector.constants.CONNECTIONS_FILE (OS specific)               |
| --connection-name CONNECTION_NAME                                                      | Override the default [connections.toml](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect#connecting-using-the-connections-toml-file) connection name. Other connection-related values will override these connection values. |
| -c CHANGE_HISTORY_TABLE, --change-history-table CHANGE_HISTORY_TABLE                   | Used to override the default name of the change history table (which is METADATA.SCHEMACHANGE.CHANGE_HISTORY)                                                                                                                                                       |
| --vars VARS                                                                            | Define values for the variables to replaced in change scripts, given in JSON format. Vars supplied via the command line will be merged with YAML-supplied vars (e.g. '{"variable1": "value1", "variable2": "value2"}')                                              |
| --create-change-history-table                                                          | Create the change history table if it does not exist. The default is 'False'.                                                                                                                                                                                       |
| -ac, --autocommit                                                                      | Enable autocommit feature for DML commands. The default is 'False'.                                                                                                                                                                                                 |
| -v, --verbose                                                                          | Display verbose debugging details during execution. The default is 'False'.                                                                                                                                                                                         |
| --dry-run                                                                              | Run schemachange in dry run mode. The default is 'False'.                                                                                                                                                                                                           |
| --query-tag                                                                            | A string to include in the QUERY_TAG that is attached to every SQL statement executed.                                                                                                                                                                              |
| --oauth-config                                                                         | Define values for the variables to Make Oauth Token requests  (e.g. {"token-provider-url": "https//...", "token-request-payload": {"client_id": "GUID_xyz",...},... })'                                                                                             |

### render

This subcommand is used to render a single script to the console. It is intended to support the development and
troubleshooting of script that use features from the jinja template engine.

`usage: schemachange render [-h] [--config-folder CONFIG_FOLDER] [-f ROOT_FOLDER] [-m MODULES_FOLDER] [--vars VARS] [-v] script`

| Parameter                                          | Description                                                                                                                               |
|----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| --config-folder CONFIG_FOLDER                      | The folder to look in for the schemachange-config.yml file (the default is the current working directory)                                 |
| -f ROOT_FOLDER, --root-folder ROOT_FOLDER          | The root folder for the database change scripts                                                                                           |
| -m MODULES_FOLDER, --modules-folder MODULES_FOLDER | The modules folder for jinja macros and templates to be used across multiple scripts                                                      |
| --vars VARS                                        | Define values for the variables to replaced in change scripts, given in JSON format (e.g. {"variable1": "value1", "variable2": "value2"}) |
| -v, --verbose                                      | Display verbose debugging details during execution (the default is False)                                                                 |

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

```
python schemachange/cli.py [-h] [--config-folder CONFIG_FOLDER] [-f ROOT_FOLDER] [-a SNOWFLAKE_ACCOUNT] [-u SNOWFLAKE_USER] [-r SNOWFLAKE_ROLE] [-w SNOWFLAKE_WAREHOUSE] [-d SNOWFLAKE_DATABASE] [-s SNOWFLAKE_SCHEMA] [-c CHANGE_HISTORY_TABLE] [--vars VARS] [--create-change-history-table] [-ac] [-v] [--dry-run] [--query-tag QUERY_TAG] [--oauth-config OUATH_CONFIG]
```

Or if installed via `pip`, it can be executed as follows:

```
schemachange [-h] [--config-folder CONFIG_FOLDER] [-f ROOT_FOLDER] [-a SNOWFLAKE_ACCOUNT] [-u SNOWFLAKE_USER] [-r SNOWFLAKE_ROLE] [-w SNOWFLAKE_WAREHOUSE] [-d SNOWFLAKE_DATABASE] [-s SNOWFLAKE_SCHEMA] [-c CHANGE_HISTORY_TABLE] [--vars VARS] [--create-change-history-table] [-ac] [-v] [--dry-run] [--query-tag QUERY_TAG] [--oauth-config OUATH_CONFIG]
```

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

<img src="images/diagram.png" alt="schemachange DevOps process" title="schemachange DevOps process" />

### Using in a CI/CD Pipeline

If your build agent has a recent version of python 3 installed, the script can be run like so:

```bash
pip install schemachange --upgrade
schemachange [-h] [-f ROOT_FOLDER] -a SNOWFLAKE_ACCOUNT -u SNOWFLAKE_USER -r SNOWFLAKE_ROLE -w SNOWFLAKE_WAREHOUSE [-d SNOWFLAKE_DATABASE] [-s SNOWFLAKE_SCHEMA] [-c CHANGE_HISTORY_TABLE] [--vars VARS] [--create-change-history-table] [-ac] [-v] [--dry-run] [--query-tag QUERY_TAG] [--oauth-config OUATH_CONFIG]
```

Or if you prefer docker, set the environment variables and run like so:

```bash
docker run -it --rm \
  --name schemachange-script \
  -v "$PWD":/usr/src/schemachange \
  -w /usr/src/schemachange \
  -e ROOT_FOLDER \
  -e SNOWFLAKE_ACCOUNT \
  -e SNOWFLAKE_USER \
  -e SNOWFLAKE_ROLE \
  -e SNOWFLAKE_WAREHOUSE \
  -e SNOWFLAKE_PASSWORD \
  python:3 /bin/bash -c "pip install schemachange --upgrade && schemachange -f $ROOT_FOLDER -a $SNOWFLAKE_ACCOUNT -u $SNOWFLAKE_USER -r $SNOWFLAKE_ROLE -w $SNOWFLAKE_WAREHOUSE"
```

Either way, don't forget to set the `SNOWFLAKE_PASSWORD` environment variable if using password authentication!

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
