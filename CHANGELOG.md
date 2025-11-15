# Changelog
All notable changes to this project will be documented in this file.

*The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).*

## [4.2.0] - TBD
### Added
- Added validation for unknown configuration keys with warning messages instead of errors for better backward and sideways compatibility (#352 by @MACKAT05)
- **New `--schemachange-initial-deployment` flag** to explicitly declare first-time deployments and prevent accidental script re-application (fixes #326)
  - CLI: `--schemachange-initial-deployment`
  - ENV: `SCHEMACHANGE_INITIAL_DEPLOYMENT`
  - YAML: `initial-deployment: true`
  - When set, validates that change history table does not exist and requires `--create-change-history-table`
  - Prevents dangerous scenario where missing table due to misconfiguration causes scripts to re-apply
  - Provides clear error messages guiding users to correct configuration
- **Migration guide** for upgrading from 4.0.x to 4.1.0+ with:
  - Complete deprecation reference table (15 CLI arguments, 3 ENV variables, 2 config parameters)
  - Quick reference table mapping deprecated to new parameter names
  - Version pinning strategy examples for controlled upgrades
  - Parameter style comparison (legacy vs. current best practices)
  - Configuration priority examples demonstrating CLI > ENV > YAML > connections.toml
  - Python code snippets for testing parameter compatibility
  - YAML v2 format examples and migration checklist
- **Troubleshooting documentation enhancements**:
  - Deprecation warning solutions with migration examples
  - Common configuration errors and fixes
  - Uppercase `.SQL` file extension clarification (#309) - documents that case-insensitive extensions are already supported
  - Unknown configuration key handling guidance
- **Demo enhancements** with authentication examples:
  - JWT (Private Key) authentication for service accounts
  - External Browser / SSO authentication for interactive use
  - OAuth token authentication for platform integrations
  - Programmatic Access Token (PAT) for MFA accounts
  - connections.toml examples for each method

### Changed
- **BREAKING**: When `--create-change-history-table` is set but change history table doesn't exist, schemachange now requires explicit `--schemachange-initial-deployment` flag (addresses #326)
  - Previously (in PR #356) would silently create table and treat all scripts as new (dangerous for accidental re-runs)
  - Now fails with clear error: "If this is the initial deployment, add --initial-deployment flag"
  - For first-time deployments: use `--create-change-history-table --schemachange-initial-deployment`
  - For subsequent deployments: ensure table exists or investigate configuration
  - This prevents dangerous scenario where missing table due to misconfiguration causes all scripts to re-apply

### Fixed
- Fixed YAML configuration validation to show warnings for unknown keys instead of throwing TypeError exceptions (#352 by @MACKAT05)

## [4.1.0] - 2025-11-14
### Added
- **New `verify` command** for testing Snowflake connectivity and displaying configuration with secrets masked. Useful for troubleshooting, CI/CD validation, and security audits. Example: `schemachange verify -C production`
- **Enhanced error handling** with user-friendly messages instead of raw tracebacks, including troubleshooting hints and proper exit codes
- **Security warnings** for insecure configurations:
  - Validates `connections.toml` file permissions (warns if world-readable)
  - Detects credentials in YAML files with remediation steps
  - Non-blocking warnings that educate on best practices
- **New documentation files**:
  - `SECURITY.md` - Authentication best practices, decision trees, security checklist
  - `TROUBLESHOOTING.md` - Common errors and solutions organized by category
- **YAML Config Version 2** with separate `schemachange` and `snowflake` sections (backward compatible with v1). See `demo/schemachange-config-v2-example.yml`
- **Comprehensive environment variable support**:
  - `SCHEMACHANGE_*` for schemachange settings (root folder, vars, log level, etc.)
  - `SNOWFLAKE_*` for connection parameters (account, user, role, warehouse, etc.)
  - Generic `SNOWFLAKE_*` pass-through for any connector parameter (e.g., `SNOWFLAKE_CLIENT_SESSION_KEEP_ALIVE`)
- **New CLI argument naming**:
  - `--schemachange-*` for schemachange parameters, `--snowflake-*` for Snowflake connection
  - New short forms: `-V` (vars), `-L` (log-level), `-Q` (query-tag), `-C` (connection-name)
  - Existing short forms retained: `-f`, `-m`, `-c`, `-ac`
- **CLI authentication arguments** (NEW in 4.1.0):
  - `--snowflake-authenticator`, `--snowflake-private-key-path`, `--snowflake-token-file-path`
  - Note: `--snowflake-private-key-passphrase` intentionally excluded (visible in process lists)
- **Authentication improvements**:
  - Programmatic Access Token (PAT) support via `SNOWFLAKE_PASSWORD` (recommended for MFA accounts)
  - OAuth token file support via `SNOWFLAKE_TOKEN_FILE_PATH`
  - Automatic whitespace handling for token files
- **Configuration precedence** clearly defined: CLI > ENV > YAML > connections.toml
- Added `--error-on-ignored-versioned-migration` flag (#287 by @zanebclark)
- Added `py.typed` marker for MyPy support (#332 by @fozcodes)
- Added `NO_COLOR` environment variable support (#357)
- Corrected `private_key_path` reference in README (#330 by @gudbrand3)

### Changed
- **Documentation updated for Snowflake's password authentication deprecation**: All docs now lead with secure methods (JWT, PAT, SSO) and include MFA warnings
- **Configuration system improvements**:
  - Unified precedence across all sources: CLI > ENV > YAML > connections.toml
  - Enhanced type conversion for environment variables (booleans, JSON, log levels)
  - Support for YAML v2 `snowflake` section and generic `SNOWFLAKE_*` pass-through
- **CLI arguments** support both old (unprefixed) and new (prefixed) forms with deprecation messages
- Updated Flyway documentation links (#333 by @sfc-gh-adamle)

### Fixed
- **Secret redaction** now properly handles configuration secrets (#312 by @zanebclark)
- **Config vars merging** now correctly includes `SCHEMACHANGE_VARS` environment variables (previously ignored)
- **JWT authentication** now works correctly in both `deploy` and `verify` commands:
  - Fixed tilde expansion for paths like `~/.snowflake/key.p8`
  - Fixed parameter naming mismatches with Snowflake connector
  - Fixed encrypted key support (no more "Expected bytes or RSAPrivateKey" errors)
- **Private key parameter names** now align with Snowflake Python Connector:
  - Use `private_key_file` instead of `private_key_path`
  - Use `private_key_file_pwd` instead of `private_key_passphrase`
  - Old names still work everywhere with helpful migration warnings
  - Works in CLI, ENV, YAML, and connections.toml
- **Session parameters from `connections.toml`** now merge correctly across all sources (CLI > ENV > YAML > connections.toml) with `QUERY_TAG` values appended instead of overridden (#355, thanks @coder-jatin-s)
- **Missing config file** now logs informative message instead of silently proceeding
- Environment variable handling improvements (contributed by @yassun7010)

### Deprecated
- **CLI arguments**: Old unprefixed forms (`--vars`, `--query-tag`, `--log-level`) deprecated in favor of `--schemachange-*` or short forms (`-V`, `-L`, `-Q`). Old forms still work with migration messages.
- **Environment variable**: `SNOWSQL_PWD` replaced by `SNOWFLAKE_PASSWORD`
- **`--verbose` flag** replaced by `--log-level` or `-L` (#288 by @zanebclark)

## [4.0.1] - 2025-02-17
### Changed
- Added back the ability to pass the Snowflake password in the `SNOWFLAKE_PASSWORD` environment variable.

## [4.0.0] - 2025-01-06
### Added
- Use of `structlog~=24.1.0` for standard log outputs
- Verified Schemachange against Python 3.12
- Support for connections.toml configurations
- Support for supplying the authenticator, private key path, token path, connections file path, and connection name via the YAML and command-line configurations.

### Changed
- Refactored the main cli.py into multiple modules - config, session.
- Updated contributing guidelines and demo readme content to help contributors setup local snowflake account to run the github actions in their fork before pushing the PR to upstream repository.
- Removed tests against Python 3.8 [End of Life on 2024-10-07](https://devguide.python.org/versions/#supported-versions)
- Command-line vars are now merged into YAML vars instead of overwriting them entirely

## [3.7.0] - 2024-07-22
### Added
- Improved unit test coverage
- Added Session ID as part of the initial connection successful message to be visible in the logs
### Changed
- Aligning with snowflake [identifier requirements](https://docs.snowflake.com/en/sql-reference/identifiers-syntax) in the configuration settings
- Fixed the bug with `Missing default warehouse`
- Fixed Demo examples resulting from change in public data set location
- Removed pandas library dependency to improve schemachange install footprint
- Updated Github Actions Workflow to check PRs and Merges does not break the demo examples.
- Updated Docs related to latest Demo content included in schemachange

## [3.6.2] - 2024-07-10
### Changed
- Updated pandas version dependency
- Pinned NumPy version dependency

## [3.6.1] - 2023-11-15
### Added
- Allow passing snowflake schema as config or CLI parameter

## [3.6.0] - 2023-09-06
### Changed
- Fixed bug introduced in version 3.5.0 where the session state was not reset after a user script was run. This resulted in schemachange updates to the metadata table failing in some cases. schemachange will now reset the session back to the default settings after each user script is run
- Updated the pytest GitHub Actions workflow
- Cleaned up whitespace and formatting in files for consistency
- Updated README file

### Added
- Added new dependency review GitHub Actions workflow
- Added badges for pytest and PyPI


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
- Added GitHub CI workflow to run unit tests and a basic execution test.
- `schemachange.cli.main` is now defined as `def main(argv: List[str]=sys.argv)`, to allow consumers to pass a list of arguments easily.

## [3.2.1] - 2021-11-04
### Fixed
- Jinja Template Engine was not recognising scripts in subfolders on Windows machines. Jinja was expecting the paths to follow a unix style ie SQL/V2.0.0__ADHOC_SCRIPT.sql but on Windows machines this was being passed through as SQL\V2.0.0__ADHOC_SCRIPT.sql.

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
- Removed the deprecated `--snowflake-region` parameter. Instead, use the `-a` or `--snowflake-account` account parameter. See [Usage Notes for the account Parameter (for the connect Method)](https://docs.snowflake.com/en/user-guide/python-connector-api.html#label-account-format-info) for more details on how to structure the account name.


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
