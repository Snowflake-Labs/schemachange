USE SCHEMA {{ SF_DATABASE }}.ETL;

CREATE OR REPLACE FUNCTION COPYINTO("TABLESCHEMA_P" VARCHAR(16777216), "TABLENAME_P" VARCHAR(16777216), "FORMAT_P" VARCHAR(16777216), "PATTERN_P" VARCHAR(16777216))
RETURNS VARCHAR(16777216)
LANGUAGE SQL
AS '
SELECT ''COPY INTO '' 
        || TableSchema_p || ''.'' || TableName_p
        || '' FROM ( '' 
        ||          '' SELECT '' 
        ||                   ( SELECT  TO_CHAR(SELECT listagg(CONCAT('' $'',to_char(ORDINAL_POSITION)), '','')  within group (order by ORDINAL_POSITION ) 
                               FROM INFORMATION_SCHEMA.COLUMNS 
                               WHERE 1=1 
                               AND TABLE_SCHEMA =   TableSchema_p 
                               AND TABLE_NAME = TableName_p 
                               AND COLUMN_NAME <> ''FILEPATH''
                              )
                    )
        || '', METADATA$FILENAME '' 
        || '' FROM @ETL.INBOUND_ETL ) '' 
        || '' FILE_FORMAT = ( FORMAT_NAME = '' 
        || format_p 
        || '') , PATTERN = '' 
        || ''\\''''|| pattern_p || ''\\'''' || '' FORCE=TRUE '' || '';''
';
