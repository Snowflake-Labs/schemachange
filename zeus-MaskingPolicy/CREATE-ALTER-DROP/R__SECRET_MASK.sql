--=============================================================================
-- PII_ADMIN ** Create/Alter Masking Policy ** 
--=============================================================================
USE ROLE PII_ADMIN;
USE DATABASE { SF_DATABASE }};

CREATE MASKING POLICY ETL.SECRET_MASK as (VAL VARCHAR) 
RETURNS VARCHAR ->
CASE
    WHEN CURRENT_ROLE() IN ('DBA','PII_RISK_ANALYST','PII_COMP_ANALYST', 'PII_DW_ENGINEER') THEN val
    WHEN VAL IS NULL THEN NULL 
    WHEN LEN(VAL) = 1 THEN NULL -- to make all DRUM character NULL
    ELSE '***Masked***'
END
;