# snowchange
<img src="images/logo.png" alt="snowchange" title="snowchange logo" width="600" />

## Overview

snowchange is a simple python based tool to manage all of your [Snowflake](https://www.snowflake.com/) objects. It follows an Imperative-style approach to Database Change Management (DCM) and was inspired by the [Flyway database migration tool](https://flywaydb.org). When combined with a version control system and a CI/CD tool, database changes can be approved and deployed through a pipeline using modern software delivery practices. As such snowchange plays a critical role in enabling Database (or Data) DevOps.

DCM tools (also known as Database Migration, Schema Change Management, or Schema Migration tools) follow one of two approaches: Declarative or Imperative. For a background on Database DevOps, including a discussion on the differences between the Declarative and Imperative approaches, please read the [Embracing Agile Software Delivery and DevOps with Snowflake](https://www.snowflake.com/blog/embracing-agile-software-delivery-and-devops-with-snowflake/) blog post.

For the complete list of changes made to snowchange check out the [CHANGELOG](CHANGELOG.md).

## Table of Contents

1. [Overview](#overview)
1. [Project Structure](#project-structure)
   1. [Folder Structure](#folder-structure)
1. [Change Scripts](#change-scripts)
   1. [Script Naming](#script-naming)
   1. [Script Requirements](#script-requirements)
1. [Change History Table](#change-history-table)
1. [Running snowchange](#running-snowchange)
   1. [Prerequisites](#prerequisites)
   1. [Running The Script](#running-the-script)
   1. [Script Parameters](#script-parameters)
1. [Getting Started with snowchange](#getting-started-with-snowchange)
1. [Integrating With DevOps](#integrating-with-devops)
   1. [Sample DevOps Process Flow](#sample-devops-process-flow)
   1. [Using in a CI/CD Pipeline](#using-in-a-cicd-pipeline)
1. [Maintainers](#maintainers)
1. [Legal](#legal)


## Installation
`pip install snowchange`

## Project Structure

### Folder Structure

snowchange expects a directory structure like the following to exist:
```
(project_root)
|
|-- folder_1
    |-- V1.1.1__first_change.sql
    |-- V1.1.2__second_change.sql
|-- folder_2
    |-- folder_3
        |-- V1.1.3__third_change.sql
```

The snowchange folder structure is very flexible. The `project_root` folder is specified with the `-f` or `--root-folder` argument. Under the `project_root` folder you are free to arrange the change scripts any way you see fit. You can have as many subfolders (and nested subfolders) as you would like.

## Change Scripts

### Script Naming

Change scripts follow a similar naming convention to that used by [Flyway Versioned Migrations](https://flywaydb.org/documentation/migrations#versioned-migrations). The script name must follow this pattern (image taken from [Flyway docs](https://flywaydb.org/documentation/migrations#versioned-migrations)):

<img src="images/flyway-naming-convention.png" alt="Flyway naming conventions" title="Flyway naming conventions" width="300" />

With the following rules for each part of the filename:

* **Prefix**: The letter 'V' for versioned change
* **Version**: A unique version number with dots or underscores separating as many number parts as you like
* **Separator**: __ (two underscores)
* **Description**: An arbitrary description with words separated by underscores or spaces (can not include two underscores)
* **Suffix**: .sql

For example, a script name that follows this convention is: `V1.1.1__first_change.sql`. As with Flyway, the unique version string is very flexible. You just need to be consistent and always use the same convention, like 3 sets of numbers separated by periods. Here are a few valid version strings:

* 1
* 5.2
* 5_2
* 1.2.3.4.5.6.7.8.9
* 205_68
* 20200115113556
* 2020.1.15.11.35.56

Every script within a database folder must have a unique version number. snowchange will check for duplicate version numbers and throw an error if it finds any. This helps to ensure that developers who are working in parallel don't accidently (re-)use the same version number.

### Script Requirements

snowchange is designed to be very lightweight and not impose to many limitations. Each change script can have any number of SQL statements within it and must supply the necessary context, like database and schema names. The context can be supplied by using an explicit `USE <DATABASE>` command or by naming all objects with a three-part name (`<database name>.<schema name>.<object name>`). snowchange will simply run the contents of each script against the target Snowflake account, in the correct order.

## Change History Table

snowchange will automatically create a change history table to track the history of all changes applied. By default the table `CHANGE_HISTORY` will be created within a `SNOWCHANGE` schema in a `METADATA` database. The name and location of the change history table can be overriden by using the `-c` (or `--change-history-table`) parameter. The value passed to the parameter can have a one, two, or three part name (e.g. "TABLE_NAME", or "SCHEMA_NAME.TABLE_NAME", or "DATABASE_NAME.SCHEMA_NAME.TABLE_NAME"). This can be used to support multiple environments (dev, test, prod) or multiple subject areas within the same Snowflake account.

The structure of the `CHANGE_HISTORY` table is as follows:

Column Name | Type |  Example
--- | --- | ---
VERSION | VARCHAR | 1.1.1
DESCRIPTION | VARCHAR | First change
SCRIPT | VARCHAR | V1.1.1__first_change.sql
SCRIPT_TYPE | VARCHAR | V
CHECKSUM | VARCHAR | 38e5ba03b1a6d2...
EXECUTION_TIME | NUMBER | 4
STATUS | VARCHAR | Success
INSTALLED_BY | VARCHAR | SNOWFLAKE_USER
INSTALLED_ON | TIMESTAMP_LTZ | 2020-03-17 12:54:33.056 -0700

A new row will be added to this table every time a change script has been applied to the database. snowchange will use this table to identify which changes have been applied to the database and will not apply the same version more than once.

## Running snowchange

### Prerequisites

In order to run snowchange you must have the following:

* You will need to have a recent version of python 3 installed
* You will need to use a user account that has permission to apply the changes in your change script

### Running the Script

snowchange is a single python script named [snowchange.py](snowchange.py). It can be executed as follows:

```
snowchange [-h] [-f ROOT_FOLDER] -a SNOWFLAKE_ACCOUNT --snowflake-region SNOWFLAKE_REGION -u SNOWFLAKE_USER -r SNOWFLAKE_ROLE -w SNOWFLAKE_WAREHOUSE  [-c CHANGE_HISTORY_TABLE] [-v] [-ac]
```

The Snowflake user password for `SNOWFLAKE_USER` is required to be set in the environment variable `SNOWSQL_PWD` prior to calling the script. snowchange will fail if the `SNOWSQL_PWD` environment variable is not set.

### Script Parameters

Here is the list of supported parameters to the script:

Parameter | Description
--- | ---
-h, --help | Show the help message and exit
-f ROOT_FOLDER, --root-folder ROOT_FOLDER| *(Optional)* The root folder for the database change scripts. The default is the current directory.
-a SNOWFLAKE_ACCOUNT, --snowflake-account SNOWFLAKE_ACCOUNT | The name of the snowflake account (e.g. ly12345)
--snowflake-region SNOWFLAKE_REGION | The name of the snowflake region (e.g. ap-southeast-2)
-u SNOWFLAKE_USER, --snowflake-user SNOWFLAKE_USER | The name of the snowflake user (e.g. DEPLOYER)
-r SNOWFLAKE_ROLE, --snowflake-role SNOWFLAKE_ROLE | The name of the role to use (e.g. DEPLOYER_ROLE)
-w SNOWFLAKE_WAREHOUSE, --snowflake-warehouse SNOWFLAKE_WAREHOUSE | The name of the warehouse to use (e.g. DEPLOYER_WAREHOUSE)
-c CHANGE_HISTORY_TABLE, --change-history-table CHANGE_HISTORY_TABLE | Used to override the default name of the change history table (e.g. METADATA.SNOWCHANGE.CHANGE_HISTORY)
-ac, --autocommit | A signal for Snowflake Python connector to enable autocommit feature for DML commands.
-v, --verbose | Display verbose debugging details during execution

## Getting Started with snowchange

The [demo](demo) folder in this project repository contains a snowchange demo project for you to try out. This demo is based on the standard Snowflake Citibike demo which can be found in [the Snowflake Hands-on Lab](https://docs.snowflake.net/manuals/other-resources.html#hands-on-lab). It contains the following database change scripts:

Change Script | Description
--- | ---
v1.1__initial_database_objects.sql | Create the initial Citibike demo objects including file formats, stages, and tables.
v1.2__load_tables_from_s3.sql | Load the Citibike and weather data from the Snowlake lab S3 bucket.

The [Citibike data](https://www.citibikenyc.com/system-data) for this demo comes from the NYC Citi Bike bike share program.

To get started with snowchange and these demo Citibike scripts follow these steps:
1. Make sure you've completed the [Prerequisites](#prerequisites) steps above
1. Get a copy of this snowchange repository (either via a clone or download)
1. Open a shell and change directory to your copy of the snowchange repository
1. Run snowchange (see [Running the Script](#running-the-script) above) with your Snowflake account details and the `demo/citibike` folder as the root folder (make sure you use the full path)

## Integrating With DevOps

### Sample DevOps Process Flow

Here is a sample DevOps development lifecycle with snowchange:

<img src="images/diagram.png" alt="snowchange DevOps process" title="snowchange DevOps process" />

### Using in a CI/CD Pipeline

If your build agent has a recent version of python 3 installed, the script can be ran like so:
```
pip install --upgrade snowflake-connector-python
python snowchange.py [-h] [-f ROOT_FOLDER] -a SNOWFLAKE_ACCOUNT --snowflake-region SNOWFLAKE_REGION -u SNOWFLAKE_USER -r SNOWFLAKE_ROLE -w SNOWFLAKE_WAREHOUSE  [-c CHANGE_HISTORY_TABLE] [-v] [-ac]
```

Or if you prefer docker, set the environment variables and run like so:
```
docker run -it --rm \
  --name snowchange-script \
  -v "$PWD":/usr/src/snowchange \
  -w /usr/src/snowchange \
  -e ROOT_FOLDER \
  -e SNOWFLAKE_ACCOUNT \
  -e SNOWFLAKE_USER \
  -e SNOWFLAKE_ROLE \
  -e SNOWFLAKE_WAREHOUSE \
  -e SNOWFLAKE_REGION \
  -e SNOWSQL_PWD \
  python:3 /bin/bash -c "pip install --upgrade snowflake-connector-python && python snowchange.py -f $ROOT_FOLDER -a $SNOWFLAKE_ACCOUNT --snowflake-region $SNOWFLAKE_REGION -u $SNOWFLAKE_USER -r $SNOWFLAKE_ROLE -w $SNOWFLAKE_WAREHOUSE"
```

Either way, don't forget to set the `SNOWSQL_PWD` environment variable!

## Maintainers

- James Weakley (@jamesweakley)
- Jeremiah Hansen (@jeremiahhansen)

This is a community-developed script, not an official Snowflake offering. It comes with no support or warranty. However, feel free to raise a github issue if you find a bug or would like a new feature.

## Legal

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this tool except in compliance with the License. You may obtain a copy of the License at: [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
