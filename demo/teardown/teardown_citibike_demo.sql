SET TARGET_DB_NAME = 'SCHEMACHANGE_DEMO'; -- Name of database that will have the SCHEMACHANGE Schema for change tracking.

-- Dependent Variables; Change the naming pattern if you want but not necessary
SET ADMIN_ROLE = $TARGET_DB_NAME || '_ADMIN'; -- This role will own the database and schemas.
SET DEPLOY_ROLE = $TARGET_DB_NAME || '_DEPLOY'; -- This role will be granted privileges to create objects in any schema in the database
SET SERVICE_USER = $TARGET_DB_NAME || '_SVC_USER'; -- This user will be granted the Deploy role.
SET WAREHOUSE_NAME = $TARGET_DB_NAME || '_WH';
SET AC_U = '_AC_U_' || $WAREHOUSE_NAME;
SET AC_O = '_AC_O_' || $WAREHOUSE_NAME;

USE ROLE IDENTIFIER($ADMIN_ROLE);

DROP DATABASE IF EXISTS IDENTIFIER($TARGET_DB_NAME);
DROP WAREHOUSE IF EXISTS IDENTIFIER($WAREHOUSE_NAME);

