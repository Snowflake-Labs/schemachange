--=============================================================================
-- PII_ADMIN ** Create/Alter Masking Policy ** 
--=============================================================================
USE ROLE PII_ADMIN;
USE DATABASE {{ SF_DATABASE }};

CREATE MASKING POLICY IF NOT EXISTS ETL.DOB_MASK_NTZ as (VAL TIMESTAMP_NTZ) 
RETURNS (VAL TIMESTAMP_NTZ) -> 
CASE
    WHEN CURRENT_ROLE() IN ('DBA','PII_RISK_ANALYST','PII_COMP_ANALYST', 'PII_DW_ENGINEER') THEN val
    WHEN VAL IS NULL THEN NULL 
    ELSE  date_from_parts(0001, 01, 01)::timestamp_ntz 
END
;

