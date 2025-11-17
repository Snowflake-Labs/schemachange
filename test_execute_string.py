#!/usr/bin/env python3
"""
Test script to understand how execute_string handles different SQL formats.
This helps diagnose issue #253.
"""


# Simulate what execute_string might do
def simulate_execute_string(sql_text):
    """
    Simulates basic statement splitting (how execute_string likely works).
    """
    print("=" * 80)
    print("INPUT SQL:")
    print("-" * 80)
    print(sql_text)
    print("=" * 80)

    # Try basic semicolon splitting
    statements = []
    current = []
    in_dollar_quote = False

    lines = sql_text.split("\n")
    for line in lines:
        stripped = line.strip()

        # Track $$ delimiters
        if "$$" in stripped:
            in_dollar_quote = not in_dollar_quote

        current.append(line)

        # If we hit a semicolon outside of $$ block, that's a statement boundary
        if ";" in stripped and not in_dollar_quote:
            statements.append("\n".join(current))
            current = []

    # Add remaining
    if current:
        statements.append("\n".join(current))

    print(f"\nSPLIT INTO {len(statements)} STATEMENTS:")
    print("-" * 80)
    for i, stmt in enumerate(statements, 1):
        print(f"\n[Statement {i}]")
        print(stmt.strip())

    return statements


# Test Case 1: Task with BEGIN...END (user's original)
print("\n\nTEST 1: Task with BEGIN...END block (user's original syntax)")
task_sql_1 = """
CREATE OR REPLACE TASK EXAMPLE_TASK
    WAREHOUSE = EXPLORATION
    SCHEDULE = '5 minutes'
AS
    BEGIN
    START TRANSACTION;
    SELECT * FROM SOME_TABLE;
    SELECT * FROM SOME_TABLE;
    COMMIT;
END;
"""
simulate_execute_string(task_sql_1)

# Test Case 2: Task with $$ delimiter
print("\n\nTEST 2: Task with $$ delimiter")
task_sql_2 = """
CREATE OR REPLACE TASK EXAMPLE_TASK
    WAREHOUSE = EXPLORATION
    SCHEDULE = '5 minutes'
AS
$$
BEGIN
    START TRANSACTION;
    SELECT * FROM SOME_TABLE;
    SELECT * FROM SOME_TABLE;
    COMMIT;
END;
$$;
"""
simulate_execute_string(task_sql_2)

# Test Case 3: Stored procedure approach
print("\n\nTEST 3: Stored procedure with $$ (should work)")
proc_sql = """
CREATE OR REPLACE PROCEDURE EXAMPLE_PROCEDURE()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    START TRANSACTION;
    SELECT * FROM SOME_TABLE;
    SELECT * FROM SOME_TABLE;
    COMMIT;
    RETURN 'Success';
END;
$$;
"""
simulate_execute_string(proc_sql)

print("\n" + "=" * 80)
print("ANALYSIS:")
print("=" * 80)
print("""
The issue is likely that execute_string() splits on semicolons INSIDE the BEGIN...END block
when $$ delimiters are NOT used (Test 1), causing parsing errors.

With $$ delimiters (Test 2), the splitting should respect the boundaries.

The stored procedure (Test 3) uses $$ and should work fine.
""")
