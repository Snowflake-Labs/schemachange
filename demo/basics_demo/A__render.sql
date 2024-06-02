use database {{ database_name }};
use schema {{ schema_name }};

use role IDENTIFIER({{ env_var('SNOWFLAKE_ROLE')}});