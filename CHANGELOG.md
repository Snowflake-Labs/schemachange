# Changelog
All notable changes to this project will be documented in this file.

*The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).*
## [3.5.4] - 2023-09-01
### Changed
- Fixed authentication workflow to check for authenticator type first, then for Key pair and finally default to password authentication.
- Fixed the `Dockerfile-src` configuration to build a docker image from source code.
- Updated README file.

## [3.5.3] - 2023-07-18
### Changed
- Updated version dependencies for `snowflake-connector-python` and `pyyaml`.

## [3.5.2] - 2023-02-14
### Changed
- Fixed bug (from the 3.5.0 release) that caused a crash when using verbose logging.

## [3.5.1] - 2023-02-11
### Changed
- Fixed a bug when handling default values from the command line with arguments defined as `action='store_true'` (create-change-history-table, auto-commit, verbose, and dry-run).

## [3.5.0] - 2023-01-29
### Added
- Added support for Oauth and external browser and Okta authentication methods.
- Added `--oauth-config` to accept values for oauth configuration.
### Changed
- Inverted Program Call sequence and refactored all snowflake interactions into a Class. Class now persists connection accross all interactions and updates the snowflake query tag session variable as scripts are executed.
- Cleaned up argument passing and other repetitive code using dictionary and set comparisons for easy maintenance. (Converted variable names to a consistent snake_case from a mix of kebab-case and snake_case)
- Fixed change history table processing to allow mixed case names when '"' are used in the name.
- Moved most error, log and warning messages and query strings to global or class variables.
- Updated readme to cover new authentication methods 

## [3.4.2] - 2022-10-24
### Changed
- Updated `snowflake-connector-python` dependency to version 2.8. This should address errors with result batching in the `fetch_r_script_checksum` method when users have a lot of scripts in their project.

## [3.4.1] - 2021-12-08
### Added
- Added a new optional parameter `--query-tag` to append a string to the QUERY_TAG that is attached to every SQL statement executed

## [3.4.0] - 2021-11-30
### Added
- Added filtering of secrets when vars are displayed on the console.
- Added filtering of secrets for deploy command when SQL statements are displayed as part of verbose output.

### Changed
- Changed vars to be pretty printed to the console.
- Changed demo citibike_jinja to demonstrate secret filtering.
- Updated the Jinja templating engine section of the README.md to document Jinja autoescaping status and added warning about untrusted input.
- Updated the table of contents section of the README.md to included missing sections.

## [3.3.3] - 2021-11-09
### Changed
- Added `env_var` Jinja function support to migration templates.
- Backed out Jinja autoescape change from 3.3.2. The default is now to have it disabled (using autoescape=False).

## [3.3.2] - 2021-11-08
### Changed
- Configured Jinja to escape inputs to templates (using autoescape=True). This helps protect rendered templates against XSS and other vulnerabilities

## [3.3.1] - 2021-11-08
### Changed
- Project is now configured with setup.cfg. There should be no change to package users.

## [3.3.0] - 2021-11-06
### Added
- Added processing of schemachange-config.yml with jinja templating engine.
  - Included new Jinja function env_var for accessing environmental variables from the config file.

## [3.2.2] - 2021-11-06
### Added
- Restored CLI tests, hopefully less fragile now.
- Added Github CI workflow to run unit tests and a basic execution test.
- `schemachange.cli.main` is now defined as `def main(argv: List[str]=sys.argv)`, to allow consumers to pass a list of arguments easily.

## [3.2.1] - 2021-11-04
### Fixed
- Jinja Template Engine was not recognising scripts in subfolders on windows machines. Jinja was expecting the paths to follow a unix style ie SQL/V2.0.0__ADHOC_SCRIPT.sql but on windows machines this was being passed through as SQL\V2.0.0__ADHOC_SCRIPT.sql.

### Removed
- Removed fragile unit tests in test_main.py.

## [3.2.0] - 2021-10-28
### Added
- Added support for jinja templates. Any file ending .sql or .sql.jinja will be processed using the [Jinja engine](https://jinja.palletsprojects.com/)
  - Added a new optional parameter `--modules-folder` to specify where common jinja template, macro or include files reside
- Added new subcommands render and deploy
  - The render command can be used to display the final script to the command line.
  - The existing functionality moved to a new deploy subcommand
  - Fall back behaviour to assume deploy sub command if none provided
- Added reserved variable name `schemachange` and an error will now be raised if supplied by the user via --vars

### Changed
- Added check for duplicate filenames. An error will now be generated should two scripts in different folders have the same name. The old behaviour resulted in just the last found script being included for execution.

## [3.1.1] - 2021-10-15
### Changed
- Loosen dependency version constraints
- Fix crash on dry run with no change history table

## [3.1.0] - 2021-09-14

### Added
- Added support for configuring schemachange through a `schemachange-config.yml` YAML file!
  - You can now invoke schemachange without supplying any command line arguments if you use the config file
  - The filename for the config file is expected to be `schemachange-config.yml`
  - Command line arguments override values in the config files
  - This also makes it easier to pass variables to your scripts
  - For more details please see the [README](README.md) for more details.
- Added a new optional parameter `--config-folder` to specify where your config file resides

## [3.0.0] - 2021-09-09

### Added
- Add Always script type (scripts that begin with the letter 'A'). Always scripts are executed with every run of schemachange

### Changed
- Fix repeatable scripts to only execute if there is a change in the script. Repeatable scripts will not be executed with every run anymore!!!
  - **IMPORTANT:** If you were relying on the existing behavior, please rename those scripts to start with the letter 'A' (see above)
- Updated versioned script filename parsing logic to use lazy regex matching for splitting version tags
  - This addresses a bug with having double underscores (__) in the description

## [2.9.4] - 2021-08-12

### Changed
- Added support for unencrypted private keys
  - `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` environment variable is no longer required if the key is not encrypted

## [2.9.3] - 2021-07-22

### Changed
- Added 'schemachange' as an application parameter when connecting, to enable usage stats.

## [2.9.2] - 2021-06-11

### Changed
- Remove requirement for running user to have CREATE SCHEMA privileges for --create-change-history-table when schema already exists (#42)

## [2.9.1] - 2021-04-15

### Changed
- Bumped snowflake-connector-python to 2.4.2 and relaxed the pip dependency to ~= (pick the latest patch release 2.4.X on install)
- Bumped the docker container python version to 3.9 as snowflake-connector-python now supports this as of 2.4
- Created a 'Dockerfile-src' for users wanting to build schemachange themselves from source in Docker

## [2.9.0] - 2021-04-02

### Changed
- Renamed snowchange to schemachange
- Please be advised that the new default path for the change history table is now `METADATA.SCHEMACHANGE.CHANGE_HISTORY` (the schema name has been changed from `SNOWCHANGE` to `SCHEMACHANGE`). The easiest thing to do is rename the metadata schema in Snowflake. The other option is to leave it as is and use the `--change-history-table` (or `-c`) parameter to override the default.


## [2.8.0] - 2021-02-09

### Added
- Added a new optional parameter `--dry-run` to preview scripts that will be applied by snowchange.


## [2.7.0] - 2021-01-22

### Added
- Added a Snowflake query tag to all snowchange queries. If the query is issued by the tool the tag will be "snowchange #.#.#" (e.g. "snowchange 2.7.0") and if the query is part of a change script the tag will be "snowchange #.#.#;&lt;script name&gt;" (e.g. "snowchange 2.7.0;V1.1.1__initial_database_objects.sql")


## [2.6.1] - 2021-01-19

### Added
- Added a new optional parameter `-d` or `--snowflake-database` to specify the default database to use (which can always be overridden in an individual change script)
- Added a new optional parameter `--create-change-history-table` to create the change history table if it does not exist

### Changed
- The default mode of operation now is to not create the change history table if it doesn't exist. Instead, now if the history table doesn't exist the tool will fail by default.
- Added a check to see if the change history table exists before trying to create it, which is now also dependent upon the `--create-change-history-table` command line argument.
- Cleaned up command line argument descriptions

### Removed
- Removed the ability for snowchange to create the database for the change history table. snowchange now requires the database to be created ahead of time.


## [2.5.0] - 2020-12-23

### Added
- Support for encrypted key pair authentication


## [2.4.0] - 2020-11-24

### Added
- PyPI package support so that snowchange can be installed through pip
- Dockerfile for building Docker images

### Changed
- Allow for .SQL file extensions (common in Windows environments) in addition to .sql extensions


## [2.3.0] - 2020-10-05

### Added
- Support for "repeatable" scripts such as stored procedures, functions etc


## [2.2.0] - 2020-08-19

### Added
- Support for variables in change scripts (following a Jinja expression syntax)! See the [README](README.md) for more details.
- A new optional parameter `--vars` which accepts a JSON formatted string of variables and values (e.g. `{"variable1": "value1", "variable2": "value2"}`)

### Changed
- Add the Snowflake account name to the script output to provide more log context

### Removed
- Removed the deprecated `--snowflake-region` parameter. Instead use the `-a` or `--snowflake-account` account parameter. See [Usage Notes for the account Parameter (for the connect Method)](https://docs.snowflake.com/en/user-guide/python-connector-api.html#label-account-format-info) for more details on how to structure the account name.


## [2.1.0] - 2020-05-26

### Added
- Support for cross-database dependencies!
- Support for override the location and name of the change history table with the new parameter `--change-history-table` (or `-c`)
- Change log for snowchange project (this CHANGELOG.md file)

### Changed
- The required project folder structure, removing the database folder convention
- Where the change history table gets created and how it gets named
- The schema of the change history table (removed INSTALLED_RANK and renamed/reordered a few columns)
- Updated the getting started section of the README.md to make the getting started steps more clear

### Removed
- The ability for snowchange to create user databases directly (now the user must explicity do so in their change scripts)
- The `--environment-name` and `--append-environment-name` parameters
