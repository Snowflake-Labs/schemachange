--=============================================================================
-- PII_ADMIN ** Create/Alter Masking Policy ** 
--=============================================================================
USE ROLE PII_ADMIN;
USE DATABASE ODIN;

ALTER MASKING POLICY ETL.DRIVERLICENSE_MASK SET BODY ->
CASE 
    WHEN CURRENT_ROLE() IN ('DBA','PII_RISK_ANALYST','PII_COMP_ANALYST', 'PII_DW_ENGINEER') THEN val
    WHEN VAL IS NULL THEN NULL 
    ELSE '***Masked***'
END
;