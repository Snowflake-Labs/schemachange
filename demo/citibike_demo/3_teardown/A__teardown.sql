SET TARGET_SCHEMA_NAME = '{{ schema_name }}';
SET TARGET_DB_NAME = '{{ database_name }}'; -- Name of database that will have the SCHEMACHANGE Schema for change tracking.
-- Dependent Variables; Change the naming pattern if you want but not necessary
SET ADMIN_ROLE = $TARGET_DB_NAME || '_ADMIN'; -- This role will own the database and schemas.
-- Including hyphen in the role to test for hyphenated role support
SET DEPLOY_ROLE = '"' || $TARGET_DB_NAME || '-DEPLOY"'; -- This role will be granted privileges to create objects in any schema in the database
SET WAREHOUSE_NAME = $TARGET_DB_NAME || '_WH';
SET SCHEMACHANGE_NAMESPACE = $TARGET_DB_NAME || '.' || $TARGET_SCHEMA_NAME;
SET SC_M = 'SC_M_' || $TARGET_SCHEMA_NAME;
SET SC_R = 'SC_R_' || $TARGET_SCHEMA_NAME;
SET SC_W = 'SC_W_' || $TARGET_SCHEMA_NAME;
SET SC_C = 'SC_C_' || $TARGET_SCHEMA_NAME;

USE ROLE IDENTIFIER($ADMIN_ROLE);
USE DATABASE IDENTIFIER($TARGET_DB_NAME);
USE SCHEMA INFORMATION_SCHEMA;

DROP SCHEMA IF EXISTS IDENTIFIER($TARGET_SCHEMA_NAME);
DROP DATABASE ROLE IF EXISTS IDENTIFIER($SC_C);
DROP DATABASE ROLE IF EXISTS IDENTIFIER($SC_W);
DROP DATABASE ROLE IF EXISTS IDENTIFIER($SC_R);
DROP DATABASE ROLE IF EXISTS IDENTIFIER($SC_M);
