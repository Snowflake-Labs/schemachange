--=============================================================================
-- PII_ADMIN ** Create/Alter Masking Policy ** 
--=============================================================================
USE ROLE PII_ADMIN;
USE DATABASE { SF_DATABASE }};

CREATE MASKING POLICY IF NOT EXISTS ETL.NAME_MASK as (VAL VARCHAR) 
RETURNS (VAL VARCHAR) ->
CASE
    WHEN CURRENT_ROLE() IN ('DBA','PII_RISK_ANALYST','PII_COMP_ANALYST', 'PII_DW_ENGINEER') THEN val
    WHEN VAL IS NULL THEN NULL 
    ELSE '***Masked***'
END
;
