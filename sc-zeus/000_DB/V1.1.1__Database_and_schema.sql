CREATE DATABASE IF NOT EXISTS {{ SF_DATABASE }} COMMENT='{{ SF_DATABASE }} Database';

USE DATABASE {{ SF_DATABASE }};

-- DW
CREATE SCHEMA IF NOT EXISTS  {{ SF_DATABASE }}.DW WITH MANAGED ACCESS	
	DEFAULT_DDL_COLLATION = 'en-ci'
	COMMENT = 'Schema for DW marts/models'
	DATA_RETENTION_TIME_IN_DAYS = 90;
-- ETL
CREATE SCHEMA IF NOT EXISTS  {{ SF_DATABASE }}.ETL WITH MANAGED ACCESS 
	DEFAULT_DDL_COLLATION = 'en-ci'
	COMMENT = 'Schema for ETL/Integrations'
	DATA_RETENTION_TIME_IN_DAYS = 90;
-- FIN
CREATE SCHEMA IF NOT EXISTS  {{ SF_DATABASE }}.FIN WITH MANAGED ACCESS 
	DEFAULT_DDL_COLLATION = 'en-ci'
	COMMENT = 'Schema for Finance/Treasury Mart'
	DATA_RETENTION_TIME_IN_DAYS = 90;
-- MKT
CREATE SCHEMA IF NOT EXISTS  {{ SF_DATABASE }}.MKT WITH MANAGED ACCESS 
	DEFAULT_DDL_COLLATION = 'en-ci'
	COMMENT = 'Schema for Marketing Mart'
	DATA_RETENTION_TIME_IN_DAYS = 90;
-- OPS
CREATE SCHEMA IF NOT EXISTS  {{ SF_DATABASE }}.OPS WITH MANAGED ACCESS 
	DEFAULT_DDL_COLLATION = 'en-ci'
	COMMENT = 'Schema for Business and Ops team processes'
	DATA_RETENTION_TIME_IN_DAYS = 90;
-- RISK
CREATE SCHEMA IF NOT EXISTS  {{ SF_DATABASE }}.RISK WITH MANAGED ACCESS 
	DEFAULT_DDL_COLLATION = 'en-ci'
	COMMENT = 'Schema for Risk Mart'
	DATA_RETENTION_TIME_IN_DAYS = 90;
-- SIGMA
CREATE SCHEMA IF NOT EXISTS {{ SF_DATABASE }}.SIGMA WITH MANAGED ACCESS 
	DEFAULT_DDL_COLLATION = 'en-ci'
	COMMENT = 'Schema for Sigma BI to read and write'
	DATA_RETENTION_TIME_IN_DAYS = 90;	
-- STG
CREATE SCHEMA IF NOT EXISTS {{ SF_DATABASE }}.STG WITH MANAGED ACCESS 
	DEFAULT_DDL_COLLATION = 'en-ci'
	COMMENT = 'Schema for S3 data'
	DATA_RETENTION_TIME_IN_DAYS = 90;
