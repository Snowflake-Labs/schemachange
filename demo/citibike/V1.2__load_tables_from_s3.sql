-- Set the database and schema context
USE SCHEMA SNOWCHANGE_DEMO.PUBLIC;

-- Load the trips data
COPY INTO TRIPS FROM @TRIPS
    FILE_FORMAT = (FORMAT_NAME = 'CSV_NO_HEADER');

-- Load the weather data
COPY INTO WEATHER FROM
    (
        SELECT
             $1
            ,CONVERT_TIMEZONE('UTC', 'US/Eastern', $1:time::TIMESTAMP_NTZ)
        FROM @WEATHER
    )
    FILE_FORMAT = (FORMAT_NAME = 'JSON');
