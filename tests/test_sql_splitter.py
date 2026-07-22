"""Tests for the BEGIN/END-aware SQL statement splitter.

These tests cover issue #421: multi-statement SQL blocks that fail because
the connector's execute_string() naively splits on semicolons.
"""

from schemachange.sql_splitter import split_sql_statements


class TestBasicSplitting:
    """Verify normal multi-statement files still split correctly."""

    def test_single_statement(self):
        sql = "SELECT 1;"
        assert split_sql_statements(sql) == ["SELECT 1;"]

    def test_single_statement_no_trailing_semicolon(self):
        sql = "SELECT 1"
        assert split_sql_statements(sql) == ["SELECT 1"]

    def test_multiple_statements(self):
        sql = "CREATE TABLE foo (id INT);\nINSERT INTO foo VALUES (1);\nSELECT * FROM foo;"
        result = split_sql_statements(sql)
        assert len(result) == 3
        assert "CREATE TABLE foo (id INT);" in result[0]
        assert "INSERT INTO foo VALUES (1);" in result[1]
        assert "SELECT * FROM foo;" in result[2]

    def test_empty_input(self):
        assert split_sql_statements("") == []

    def test_whitespace_only(self):
        assert split_sql_statements("   \n\n  ") == []

    def test_semicolons_only(self):
        assert split_sql_statements(";;;") == []


class TestBeginEndBlocks:
    """Core tests for BEGIN...END block detection."""

    def test_procedure_with_as_begin(self):
        sql = """CREATE OR REPLACE PROCEDURE powerbi.refresh_hc_bridge()
RETURNS VARCHAR
LANGUAGE SQL
AS
BEGIN
    TRUNCATE TABLE powerbi.hc_bridge;
    INSERT INTO powerbi.hc_bridge
    SELECT * FROM source_table;
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_task_with_as_begin(self):
        sql = """CREATE OR REPLACE TASK my_task
  WAREHOUSE = my_warehouse
  SCHEDULE = '5 minutes'
AS
BEGIN
  START TRANSACTION;
  SELECT * FROM table1;
  COMMIT;
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_anonymous_block_standalone(self):
        """Anonymous block at statement start (no AS/DO prefix)."""
        sql = """BEGIN
    LET x := 42;
    INSERT INTO t1 VALUES (:x);
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_nested_begin_end(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR
LANGUAGE SQL
AS
BEGIN
    IF (TRUE) THEN
        BEGIN
            INSERT INTO t1 VALUES (1);
        END;
    END IF;
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_deeply_nested(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR
LANGUAGE SQL
AS
BEGIN
    IF (x > 0) THEN
        BEGIN
            FOR i IN 1..10 LOOP
                BEGIN
                    INSERT INTO t1 VALUES (:i);
                END;
            END LOOP;
        END;
    END IF;
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_anonymous_block_after_other_statement(self):
        """Anonymous BEGIN block following another statement in the same file."""
        sql = """EXECUTE IMMEDIATE 'some dynamic sql';
BEGIN
    LET x := 1;
    INSERT INTO t VALUES (:x);
END;"""
        result = split_sql_statements(sql)
        # Two statements: EXECUTE IMMEDIATE and the anonymous BEGIN block
        assert len(result) == 2


class TestDeclareBeginBlocks:
    """DECLARE...BEGIN pattern must be treated as a single block."""

    def test_declare_begin_anonymous_block(self):
        """From Snowflake docs: anonymous block with DECLARE section."""
        sql = """DECLARE
  radius_of_circle FLOAT;
  area_of_circle FLOAT;
BEGIN
  radius_of_circle := 3;
  area_of_circle := PI() * radius_of_circle * radius_of_circle;
  RETURN area_of_circle;
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_procedure_with_as_declare_begin(self):
        """From Snowflake docs: procedure with AS DECLARE...BEGIN."""
        sql = """CREATE OR REPLACE PROCEDURE area()
RETURNS FLOAT
LANGUAGE SQL
AS
DECLARE
  radius FLOAT;
  area_of_circle FLOAT;
BEGIN
  radius := 3;
  area_of_circle := PI() * radius * radius;
  RETURN area_of_circle;
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_declare_does_not_trigger_on_identifier(self):
        """DECLARE as part of a table/column name should not trigger block detection."""
        sql = """CREATE TABLE declare_test (id INT);
SELECT * FROM declare_test;"""
        result = split_sql_statements(sql)
        assert len(result) == 2

    def test_declare_with_exception_handler(self):
        """DECLARE...BEGIN...EXCEPTION...END pattern."""
        sql = """DECLARE
  my_exception EXCEPTION (-20001, 'Something went wrong');
BEGIN
  INSERT INTO t1 VALUES (1);
EXCEPTION
  WHEN my_exception THEN
    RETURN 'Error handled';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1


class TestElseBegin:
    """ELSE BEGIN blocks must be handled correctly."""

    def test_else_begin(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR LANGUAGE SQL AS
BEGIN
    IF (FALSE) THEN
        RETURN 'no';
    ELSE
        BEGIN
            INSERT INTO t1 VALUES (1);
        END;
    END IF;
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1


class TestBeginTransactionNotBlocked:
    """BEGIN TRANSACTION/WORK must NOT be treated as block openers."""

    def test_begin_transaction(self):
        sql = """BEGIN TRANSACTION;
INSERT INTO foo VALUES (1);
COMMIT;"""
        result = split_sql_statements(sql)
        assert len(result) == 3

    def test_begin_work(self):
        sql = """BEGIN WORK;
INSERT INTO foo VALUES (1);
COMMIT;"""
        result = split_sql_statements(sql)
        assert len(result) == 3

    def test_begin_transaction_case_insensitive(self):
        sql = """begin transaction;
insert into foo values (1);
commit;"""
        result = split_sql_statements(sql)
        assert len(result) == 3


class TestCompoundEndKeywords:
    """END IF, END LOOP, END FOR, END WHILE should not decrement depth."""

    def test_end_if_does_not_close_begin(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR LANGUAGE SQL AS
BEGIN
    IF (TRUE) THEN
        INSERT INTO t1 VALUES (1);
    END IF;
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_end_loop_does_not_close_begin(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR LANGUAGE SQL AS
BEGIN
    FOR i IN 1..5 LOOP
        INSERT INTO t1 VALUES (:i);
    END LOOP;
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_end_case_does_not_close_begin(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR LANGUAGE SQL AS
BEGIN
    CASE
        WHEN x = 1 THEN INSERT INTO t1 VALUES (1);
        ELSE INSERT INTO t1 VALUES (0);
    END CASE;
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1


class TestDollarQuoting:
    """Dollar-quoted blocks should be preserved as-is."""

    def test_dollar_quoted_procedure(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    SELECT 1;
    RETURN 'OK';
END;
$$;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_execute_immediate_dollar_quoted(self):
        sql = """EXECUTE IMMEDIATE $$
BEGIN
    TRUNCATE TABLE t1;
    INSERT INTO t1 SELECT * FROM src;
END;
$$;"""
        result = split_sql_statements(sql)
        assert len(result) == 1


class TestCommentsAndStrings:
    """Semicolons in comments and strings must not cause splits."""

    def test_semicolon_in_single_line_comment(self):
        sql = """SELECT 1 -- this has a ; semicolon
;
SELECT 2;"""
        result = split_sql_statements(sql)
        assert len(result) == 2

    def test_semicolon_in_block_comment(self):
        sql = """SELECT 1 /* this ; has ; semicolons */;
SELECT 2;"""
        result = split_sql_statements(sql)
        assert len(result) == 2

    def test_semicolon_in_string_literal(self):
        sql = """SELECT 'hello;world';
SELECT 'foo;bar';"""
        result = split_sql_statements(sql)
        assert len(result) == 2

    def test_begin_in_string_not_treated_as_block(self):
        sql = """SELECT 'BEGIN';
SELECT 'END';"""
        result = split_sql_statements(sql)
        assert len(result) == 2

    def test_begin_in_comment_not_treated_as_block(self):
        sql = """-- BEGIN
SELECT 1;
-- END
SELECT 2;"""
        result = split_sql_statements(sql)
        assert len(result) == 2


class TestEdgeCases:
    """Edge cases from the 11 consolidated issues."""

    def test_dynamic_table_with_subquery(self):
        """Issue #203, #262 — dynamic tables with complex definitions."""
        sql = """CREATE OR REPLACE DYNAMIC TABLE my_dt
  TARGET_LAG = '1 hour'
  WAREHOUSE = my_wh
AS
  SELECT a.id, b.name
  FROM table_a a
  JOIN table_b b ON a.id = b.id;"""
        result = split_sql_statements(sql)
        # This is a single statement (AS introduces a subquery, not a BEGIN block)
        assert len(result) == 1

    def test_procedure_followed_by_grant(self):
        """Multiple statements where one contains BEGIN...END."""
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR LANGUAGE SQL AS
BEGIN
    INSERT INTO t1 VALUES (1);
    RETURN 'OK';
END;
GRANT USAGE ON PROCEDURE foo() TO ROLE analyst;"""
        result = split_sql_statements(sql)
        assert len(result) == 2
        assert "CREATE OR REPLACE PROCEDURE" in result[0]
        assert "GRANT USAGE" in result[1]

    def test_multiple_procedures_in_one_file(self):
        sql = """CREATE OR REPLACE PROCEDURE proc_a()
RETURNS VARCHAR LANGUAGE SQL AS
BEGIN
    RETURN 'A';
END;

CREATE OR REPLACE PROCEDURE proc_b()
RETURNS VARCHAR LANGUAGE SQL AS
BEGIN
    RETURN 'B';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 2
        assert "proc_a" in result[0]
        assert "proc_b" in result[1]

    def test_escaped_quotes_in_string(self):
        sql = """INSERT INTO t1 VALUES ('it''s a test;');
SELECT 1;"""
        result = split_sql_statements(sql)
        assert len(result) == 2


class TestCommentsBeforeBegin:
    """Comments between AS and BEGIN must not break block detection."""

    def test_line_comment_between_as_and_begin(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR LANGUAGE SQL
AS
-- This is a comment
BEGIN
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_multiple_line_comments_between_as_and_begin(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR LANGUAGE SQL
AS
-- Comment line 1
-- Comment line 2
BEGIN
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_inline_comment_after_as(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR LANGUAGE SQL AS -- inline comment
BEGIN
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_block_comment_between_as_and_begin(self):
        sql = """CREATE OR REPLACE PROCEDURE foo()
RETURNS VARCHAR LANGUAGE SQL
AS
/* This is a
   multi-line block comment */
BEGIN
    RETURN 'OK';
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1


class TestIdentifierBoundaries:
    """BEGIN/END/DECLARE as part of identifiers must not trigger."""

    def test_begin_in_identifier(self):
        sql = "SELECT BEGIN_DATE, WEEKEND FROM my_table;"
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_end_in_identifier(self):
        sql = "SELECT BACKEND, FRONTEND FROM my_table;"
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_begin_end_in_double_quotes(self):
        sql = """SELECT "BEGIN", "END" FROM my_table;
SELECT 1;"""
        result = split_sql_statements(sql)
        assert len(result) == 2


class TestLoopPatterns:
    """Test all Snowflake loop types from docs."""

    def test_for_loop_with_do(self):
        sql = """DECLARE
  counter INTEGER DEFAULT 0;
  maximum_count INTEGER default 5;
BEGIN
  FOR i IN 1 TO maximum_count DO
    counter := counter + 1;
  END FOR;
  RETURN counter;
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_while_loop_with_do(self):
        sql = """BEGIN
  LET counter := 0;
  WHILE (counter < 5) DO
    counter := counter + 1;
  END WHILE;
  RETURN counter;
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_repeat_loop(self):
        sql = """BEGIN
  LET counter := 5;
  REPEAT
    counter := counter - 1;
  UNTIL (counter = 0)
  END REPEAT;
  RETURN counter;
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_loop_with_break(self):
        sql = """BEGIN
  LET counter := 5;
  LOOP
    IF (counter = 0) THEN
      BREAK;
    END IF;
    counter := counter - 1;
  END LOOP;
  RETURN counter;
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1

    def test_nested_loops_with_labels(self):
        sql = """BEGIN
  LET inner_counter := 0;
  LET outer_counter := 0;
  LOOP
    LOOP
      IF (inner_counter < 5) THEN
        inner_counter := inner_counter + 1;
        CONTINUE OUTER;
      ELSE
        BREAK OUTER;
      END IF;
    END LOOP INNER;
    outer_counter := outer_counter + 1;
    BREAK;
  END LOOP OUTER;
  RETURN ARRAY_CONSTRUCT(outer_counter, inner_counter);
END;"""
        result = split_sql_statements(sql)
        assert len(result) == 1
