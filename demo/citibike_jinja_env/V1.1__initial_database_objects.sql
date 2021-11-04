-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS SCHEMACHANGE_DEMO;

-- Set the database and schema context
USE SCHEMA SCHEMACHANGE_DEMO.PUBLIC;

-- Create the file formats
CREATE OR REPLACE FILE FORMAT CSV_NO_HEADER
    TYPE='CSV'
    COMPRESSION = 'AUTO'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 0
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('NULL','\\N','\N', '');

CREATE OR REPLACE FILE FORMAT JSON
    TYPE='JSON'
    COMPRESSION = 'AUTO'
    ENABLE_OCTAL = FALSE
    ALLOW_DUPLICATE = FALSE
    STRIP_OUTER_ARRAY = FALSE
    STRIP_NULL_VALUES = FALSE
    IGNORE_UTF8_ERRORS = FALSE;

-- Create the stages

-- Stages located in S3 require AWS_KEY_ID and AWS_SECRET_KEY
-- to be specified (if no STORAGE INTEGRATION exists)
-- If these are specified in `--vars` they will be printed to stdout,
-- so we want to get these directly from environment.
-- If not found in environment, falls back to checking vars.
CREATE OR REPLACE STAGE TRIPS
    URL = 's3://snowflake-workshop-lab/citibike-trips'
    CREDENTIALS = (
        AWS_KEY_ID = '{{ aws_s3_access_key | from_environ("AWS_S3_ACCESS_KEY") }}',
        AWS_SECRET_KEY = '{{ aws_s3_secret_key | from_environ("AWS_S3_ACCESS_KEY") }}'
    );

CREATE OR REPLACE STAGE WEATHER
    URL = 's3://snowflake-workshop-lab/weather-nyc';

-- Create the tables
CREATE OR REPLACE TABLE TRIPS
(
     TRIPDURATION INTEGER
    ,STARTTIME TIMESTAMP
    ,STOPTIME TIMESTAMP
    ,START_STATION_ID INTEGER
    ,START_STATION_NAME STRING
    ,START_STATION_LATITUDE FLOAT
    ,START_STATION_LONGITUDE FLOAT
    ,END_STATION_ID INTEGER
    ,END_STATION_NAME STRING
    ,END_STATION_LATITUDE FLOAT
    ,END_STATION_LONGITUDE FLOAT
    ,BIKEID INTEGER
    ,MEMBERSHIP_TYPE STRING
    ,USERTYPE STRING
    ,BIRTH_YEAR INTEGER
    ,GENDER INTEGER
);

CREATE OR REPLACE TABLE WEATHER
(
     V VARIANT
    ,T TIMESTAMP
);
