use database {{ database_name }};
use schema {{ schema_name }};

create transient table FORGETMEPLEASE (
    test varchar
);

-- comment in the last line
-- Adding query to avoid last comment line.
SELECT 1;
