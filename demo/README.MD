# Demo

The contents of this Demo serves two audiences - Consumers and Contributors. For the Consumer, the demo provides a basis on which you can see how schemachange works with the main feature set. For the contributor, who forks the repo and submits PRs to the codebase, this will serve as a basis to test the PR against your own snowflake account to ensure your code change does not break any existing functionality.

## Prequisite

- You will need your own snowflake Account to test the Demo. 

### Contributors
- If you are a Contributor, you will have to set up scehamchange demo database and schemachange schema (See Initialize and Setup scripts below). Alongthen set up the following Secrets in your forked repository 
    - SCHEMACHANGE_SNOWFLAKE_PASSWORD
    - SCHEMACHANGE_SNOWFLAKE_USER
    - SCHEMACHANGE_SNOWFLAKE_ACCOUNT

### Consumers
- If you are consumer who is installing schemachange and wants to test-run the demo, then you will have to set the following environment variables.
    - SNOWFLAKE_ACCOUNT
    - SNOWFLAKE_USER
    - SNOWFLAKE_PASSWORD
    - SCENARIO_NAME
    - SNOWFLAKE_WAREHOUSE Keyed to SCHEMACHANGE_DEMO_WH
    - SNOWFLAKE_DATABASE Keyed to SCHEMACHANGE_DEMO
    - SNOWFLAKE_ROLE Keyed to SCHEMACHANGE_DEMO_DEPLOY
    
The scripts in the `provision` folder are to be used to setup up your demo database along with a schema in that database that will house the change tracking tables needed to setup and teardown the schemas used to test a working version of the demo DDL scripts.
The [initialize](provision/initialize.sql) script setups the database, warehouse and account level access roles that will be used on the 
The [setup](provision/setup_schemachange_schema.sql) script creates the `SCHEMACHANGE` schema in the database that you created in the initialize step.

# Setup


# Teardown

# 
# citibike

# citibike jinja