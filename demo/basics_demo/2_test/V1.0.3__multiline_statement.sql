-- =============================================================================
-- Demo: Multi-statement SQL blocks (NEW in schemachange 4.4.0)
--
-- Prior to 4.4.0, these patterns required $$...$$ workarounds because the
-- connector split on semicolons client-side. The new BEGIN/END-aware SQL
-- splitter handles them natively.
-- =============================================================================

-- 1. Stored procedure with BEGIN...END (no $$ needed)
CREATE OR REPLACE PROCEDURE {{ database_name }}.{{ schema_name }}.demo_refresh_proc()
RETURNS VARCHAR
LANGUAGE SQL
AS
BEGIN
    TRUNCATE TABLE {{ database_name }}.{{ schema_name }}.demo_target;
    INSERT INTO {{ database_name }}.{{ schema_name }}.demo_target
        SELECT CURRENT_TIMESTAMP() AS refreshed_at, 'batch_1' AS source;
    RETURN 'Refresh complete';
END;

-- 2. Task with multi-statement body (the #1 requested pattern from issue #421)
CREATE OR REPLACE TASK {{ database_name }}.{{ schema_name }}.demo_refresh_task
    WAREHOUSE = {{ warehouse_name }}
    SCHEDULE = 'USING CRON 0 6 * * * America/New_York'
AS
BEGIN
    CALL {{ database_name }}.{{ schema_name }}.demo_refresh_proc();
    INSERT INTO {{ database_name }}.{{ schema_name }}.demo_audit_log
        VALUES (CURRENT_TIMESTAMP(), 'demo_refresh_task', 'completed');
END;

-- 3. Anonymous block with DECLARE section
DECLARE
    row_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO row_count FROM {{ database_name }}.{{ schema_name }}.demo_target;
    IF (row_count = 0) THEN
        INSERT INTO {{ database_name }}.{{ schema_name }}.demo_target
            VALUES (CURRENT_TIMESTAMP(), 'seed_data');
    END IF;
END;
