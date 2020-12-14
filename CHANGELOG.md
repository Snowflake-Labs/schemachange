# Changelog
All notable changes to this project will be documented in this file.

*The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).*

## [2.5.0] - 2020-12-14

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
