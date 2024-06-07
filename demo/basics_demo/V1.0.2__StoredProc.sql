-- This block of code executes in Visual Studio Code but fails in Schemachange.
-- Use the $$ ... $$ to mark the block and execute the code block successfully.
-- The comment from a community user help find the root cause.
-- Link to comment: https://github.com/Snowflake-Labs/schemachange/issues/212#issuecomment-2052187227

CREATE OR REPLACE PROCEDURE output_message(message VARCHAR)
RETURNS VARCHAR NOT NULL
LANGUAGE SQL
AS
$$
BEGIN
  RETURN message;
END;
$$;
