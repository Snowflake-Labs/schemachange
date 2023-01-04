--=============================================================================
-- PII_ADMIN ** Create/Alter Masking Policy ** 
--=============================================================================
USE ROLE PII_ADMIN;
USE DATABASE ODIN;

ALTER MASKING POLICY ETL.SSN_MASK SET BODY ->
CASE
    WHEN CURRENT_ROLE() IN ('DBA','PII_RISK_ANALYST','PII_COMP_ANALYST', 'PII_DW_ENGINEER') THEN val
    WHEN LEN(VAL) < 9 THEN NULL
    ELSE  sha2(val,'256')
END
;