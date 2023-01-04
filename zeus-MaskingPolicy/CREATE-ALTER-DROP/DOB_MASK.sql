--=============================================================================
-- PII_ADMIN ** Create/Alter Masking Policy ** 
--=============================================================================
USE ROLE PII_ADMIN;
USE DATABASE ODIN;

-- This policy was discontinued and replace with DOB_MASK_DT, need to drop it from ODIN.
DROP POLICY ETL.DOB_MASK;
