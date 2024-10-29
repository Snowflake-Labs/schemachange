# Demo

The contents of this Demo serves two audiences - Consumers and Contributors. For the Consumer, the demo provides a basis
to see how schemachange works with the main feature set. For the contributor, who forks the repo and submits PRs to the
codebase, this will serve as a basis to test the PR against your own snowflake account to ensure your code change does
not break any existing functionality.

## Prerequisite

- You will need your own snowflake Account to test the Demo - Both as a contributor and consumer.
- You will need to review and run statements in the provision folder or set up your own database and schema.
    - [initialize.sql](provision/initialize.sql): Contains the SQL variables to initialize your environment.
    - [setup_schemachange_schema.sql](provision/setup_schemachange_schema.sql): Contains the SQL variables to track the
      individual demo scenarios in its own change history table.

### Contributors

As a contributor, you will have to set up schemachange demo database and schemachange schema (See Initialize and Setup
scripts below). Along with that you will also set up the following Secrets in your forked repository so that the GitHub
actions can set up, test and teardown the temporary schema it creates to test the changes to your code in the master and
dev branches respectively.

- SCHEMACHANGE_SNOWFLAKE_PASSWORD
- SCHEMACHANGE_SNOWFLAKE_USER
- SCHEMACHANGE_SNOWFLAKE_ACCOUNT

### Consumers

- If you are consumer who is installing schemachange and wants to test-run the demo, then you will have to set the
  following environment variables.
    - SNOWFLAKE_ACCOUNT: This will be the account identifier for your Snowflake account.
    - SNOWFLAKE_USER: This will be the user that will connect to your snowflake account (`SNOWFLAKE_ACCOUNT`).
    - SNOWFLAKE_PASSWORD: This is the password for the user (`SNOWFLAKE_USER`) that will connect to your snowflake account (`SNOWFLAKE_ACCOUNT`).
    - SCENARIO_NAME: This will be demo folder you intend to experiment with. For
      starters, `basics_demo`, `citibike_demo` or `citibike_demo_jinja` are included with the repo that will set the
      root folder value in the respective schemachange-config.yml file.
    - SNOWFLAKE_WAREHOUSE: This will be the warehouse you set up for the demo. Default setup is SCHEMACHANGE_DEMO_WH. You can update this to your warehouse in your snowflake account (`SNOWFLAKE_ACCOUNT`).
    - SNOWFLAKE_DATABASE Keyed to SCHEMACHANGE_DEMO. You can update this to the database in your snowflake account (`SNOWFLAKE_ACCOUNT`)
    - SNOWFLAKE_ROLE Keyed to SCHEMACHANGE_DEMO-DEPLOY. This particular role name was chosen to test hyphenated roles in schemachange. You can update this value to match the role you have setup in your snowflake account (`SNOWFLAKE_ACCOUNT`).

Either you setup Warehouse, Database and role to match the demo defaults and run the demo as is pointing to your account (`SNOWFLAKE_ACCOUNT`) or update the schemachange-config.yml file keys to match values you have setup in your local snowflake account and run the demo scenarios to get a feel for how schemachange works.

The scripts in the `provision` folder can be used to set up up your demo database along with a schema in that database
that will house the change tracking tables needed to set up and teardown the schemas used to test a working version of
the demo DDL scripts.

- The [initialize](provision/initialize.sql) script setups the database, warehouse and account level access roles that
  will be used on the
- The [setup](provision/setup_schemachange_schema.sql) script creates the `SCHEMACHANGE` schema in the database that you
  created in the initialize step.

# Setup

The setup scripts are included to build the schema needed by the GitHub Actions Workflow to avoid conflict across jobs
when tested in parallel. The Setup script will create a new schema to run the schemachange script for the corresponding
scenario.

# Teardown

The Teardown scripts are the bookend pairing of the Setup script for each scenario so that when the build process is
done using GitHub actions, you will have a log of the testing done to ensure that schemachange is working as expected.
