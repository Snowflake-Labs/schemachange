-- Set the database and schema context
USE SCHEMA SCHEMACHANGE_DEMO.CITIBIKE_DEMO;

-- Load the trips data
-- Trips data bucket content has been updated. 
-- https://stackoverflow.com/questions/72235656/snowflake-trial-data-in-wrong-format
COPY INTO TRIPS FROM @TRIPS
    FILE_FORMAT = (FORMAT_NAME = 'CSV_NO_HEADER')
    PATTERN = '.*trips_.*csv.gz';

-- Load the weather data
COPY INTO WEATHER FROM
    (
        SELECT
             $1
            ,CONVERT_TIMEZONE('UTC', 'US/Eastern', $1:time::TIMESTAMP_NTZ)
        FROM @WEATHER
    )
    FILE_FORMAT = (FORMAT_NAME = 'JSON');
