-- This script is provided as a sample setup to use database roles, warehouse, admin role, deploy role as an example.
-- YOu may choose to have your own RBAC and SCHEMACHANGE database setup depending on your organization objectives.
-- Set these to personalize your deployment
SET SERVICE_USER_PASSWORD = 'CHANGEME';
SET ADMIN_USER = 'CHANGEME';
SET TARGET_DB_NAME = 'SCHEMACHANGE_DEMO'; -- Name of database that will have the SCHEMACHANGE Schema for change tracking.

-- Dependent Variables; Change the naming pattern if you want but not necessary
SET ADMIN_ROLE = $TARGET_DB_NAME || '_ADMIN'; -- This role will own the database and schemas.
-- The deploy role is name with hyphen is used to allow us to test the use of hyphenated identifiers.
SET DEPLOY_ROLE = '"' || $TARGET_DB_NAME || '-DEPLOY"'; -- This role will be granted privileges to create objects in any schema in the database
SET SERVICE_USER = $TARGET_DB_NAME || '_SVC_USER'; -- This user will be granted the Deploy role.
SET WAREHOUSE_NAME = $TARGET_DB_NAME || '_WH';
SET AC_U = '_AC_U_' || $WAREHOUSE_NAME;
SET AC_O = '_AC_O_' || $WAREHOUSE_NAME;

USE ROLE USERADMIN;
-- Service user used to run SCHEMACHANGE deployments
CREATE USER IF NOT EXISTS IDENTIFIER($SERVICE_USER) WITH PASSWORD=$SERVICE_USER_PASSWORD MUST_CHANGE_PASSWORD=FALSE;
-- Role granted to a human user to manage the database permissions and database roles.
CREATE ROLE IF NOT EXISTS IDENTIFIER($ADMIN_ROLE);
CREATE ROLE IF NOT EXISTS IDENTIFIER($DEPLOY_ROLE);
CREATE ROLE IF NOT EXISTS IDENTIFIER($AC_U);
CREATE ROLE IF NOT EXISTS IDENTIFIER($AC_O);
GRANT ROLE IDENTIFIER($AC_U) TO ROLE IDENTIFIER($AC_O);


-- Role hierarchy tied to SYSADMIN;
USE ROLE SECURITYADMIN;
GRANT ROLE IDENTIFIER($DEPLOY_ROLE) TO ROLE IDENTIFIER($ADMIN_ROLE);
GRANT ROLE IDENTIFIER($ADMIN_ROLE) TO ROLE SYSADMIN;

GRANT ROLE IDENTIFIER($ADMIN_ROLE) TO USER IDENTIFIER($SERVICE_USER);
GRANT ROLE IDENTIFIER($ADMIN_ROLE) TO USER IDENTIFIER($ADMIN_USER);

USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS IDENTIFIER($TARGET_DB_NAME);

USE ROLE SECURITYADMIN;
GRANT OWNERSHIP ON DATABASE IDENTIFIER($TARGET_DB_NAME) TO ROLE IDENTIFIER($ADMIN_ROLE) WITH GRANT OPTION;

USE ROLE SYSADMIN;
CREATE WAREHOUSE IF NOT EXISTS IDENTIFIER($WAREHOUSE_NAME);
USE ROLE SECURITYADMIN;
GRANT OWNERSHIP ON WAREHOUSE IDENTIFIER($WAREHOUSE_NAME) TO ROLE IDENTIFIER($ADMIN_ROLE) WITH GRANT OPTION;
GRANT USAGE ON WAREHOUSE IDENTIFIER($WAREHOUSE_NAME) TO ROLE IDENTIFIER($AC_U);
GRANT OPERATE ON WAREHOUSE IDENTIFIER($WAREHOUSE_NAME) TO ROLE IDENTIFIER($AC_O);
GRANT ROLE IDENTIFIER($AC_U) TO ROLE IDENTIFIER($DEPLOY_ROLE);
