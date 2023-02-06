--=============================================================================
-- PII_ADMIN ** Create/Alter Masking Policy ** 
--=============================================================================
USE ROLE PII_ADMIN;
USE DATABASE {{ SF_DATABASE }};

CREATE MASKING POLICY IF NOT EXISTS ETL.ADDRESS_MASK as (VAL VARCHAR) 
returns (VAL VARCHAR) ->
CASE
    WHEN CURRENT_ROLE() IN ('DBA','PII_RISK_ANALYST','PII_COMP_ANALYST', 'PII_DW_ENGINEER') THEN val
    WHEN VAL IS NULL THEN NULL 
    ELSE '***Masked***'
END
;
