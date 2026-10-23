-- Demo: Inline comment on the same line as the final semicolon
-- schemachange appends a no-op SELECT 1; for execution only, so the comment is kept
-- and Snowflake does not reject it as an empty statement. The checksum is unaffected.

use database {{ database_name }};
use schema {{ schema_name }};

SELECT 'Inline comment with semicolon'; -- inline comment is fine
