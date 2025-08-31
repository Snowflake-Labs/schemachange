-- Teardown script for LocalDataInjection demo
USE DATABASE {{database_name}};
USE SCHEMA {{database_name}}.{{schema_name}};

-- Drop tables
DROP TABLE IF EXISTS TRIPS;
DROP TABLE IF EXISTS WEATHER;

-- Drop file formats
DROP FILE FORMAT IF EXISTS CSV_NO_HEADER;
DROP FILE FORMAT IF EXISTS JSON;

-- Drop stages
DROP STAGE IF EXISTS TRIPS;
DROP STAGE IF EXISTS WEATHER;
