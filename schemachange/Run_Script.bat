@ECHO OFF
:: Assign all SNOWFLAKE variables
SET SNOWFLAKE_ACCOUNT=curoorg-curo
SET SNOWFLAKE_USER=SVC_SC_ARES
SET SNOWFLAKE_ROLE=DW_ENGINEER
SET SNOWFLAKE_WAREHOUSE=DW_WH
SET SNOWFLAKE_PASSWORD=5_1ADlfE?ObU9eCa*uGL
:: DEFAULT DATABASE 
SET SNOWFLAKE_DATABASE=ARES_DB

:: User Database 
ECHO ===================================================================================================
SET /p SC_CHANGE_HISTORY=Enter Database Name where CHANGE_HISTORY table resides? 
SET /p USER_DATABASE=Enter Database Name would you like to run SchemaChange against? 
SET /p SF_TEST_STORAGE_INTEGRATION=Enter Test SI now:
SET /p SF_TEST_S3_ETLDATA_URL=Enter Test S3 URL:
@REM SET /P FR_STORY=Enter FreshRelase Story Number : 

PAUSE
ECHO ===================================================================================================


SET VARS="{""SF_DATABASE"":""%USER_DATABASE%"",""SF_STORAGE_INTEGRATION"":""%SF_TEST_STORAGE_INTEGRATION%"",""SF_S3_ETLDATA_URL"":""%SF_TEST_S3_ETLDATA_URL%""}"

:: ECHO all SNOWFLAKE variables
ECHO ===================================================================================================
ECHO ACCOUNT        : %SNOWFLAKE_ACCOUNT%
ECHO USER           : %SNOWFLAKE_USER%
ECHO ROLE           : %SNOWFLAKE_ROLE%
ECHO WAREHOUSE      : %SNOWFLAKE_WAREHOUSE%
ECHO DEFAULT DB     : %SNOWFLAKE_DATABASE%
ECHO VARS           : %VARS%
ECHO ***********************************************
ECHO ***********************************************
ECHO CHANGE_HISTORY DB     : %SC_CHANGE_HISTORY%
ECHO Applying Change to DB : %USER_DATABASE%
ECHO Freshrelease Story    : %FR_STORY%
ECHO ***********************************************
ECHO ***********************************************
PAUSE
ECHO ===================================================================================================
ECHO ===================================================================================================
ECHO Running SchemChange now ...

SET CWD=%cd%
SET CWD_ZEUS=%CWD:schemachange\schemachange=schemachange\sc-zeus%

cd %CWD%
@REM python cli.py -f %CWD_ZEUS% -a %SNOWFLAKE_ACCOUNT% -u %SNOWFLAKE_USER% -r %SNOWFLAKE_ROLE% -w %SNOWFLAKE_WAREHOUSE% -d %SNOWFLAKE_DATABASE% --vars %VARS% --create-change-history-table --query-tag SMC-%FR_STORY%
python .\schemachange\cli.py -f .\sc-zeus -a %SNOWFLAKE_ACCOUNT% -u %SNOWFLAKE_USER% -r %SNOWFLAKE_ROLE% -w %SNOWFLAKE_WAREHOUSE% -d %SNOWFLAKE_DATABASE% --vars %VARS% -c %SC_CHANGE_HISTORY%.SCHEMACHANGE.CHANGE_HISTORY --create-change-history-table --query-tag SMC-%FR_STORY%
ECHO ===================================================================================================
PAUSE