"""BEGIN/END-aware SQL statement splitter for schemachange.

Replaces the Snowflake Python connector's `execute_string()` splitting,
which naively splits on semicolons and breaks multi-statement blocks like
stored procedures, tasks, and anonymous blocks that use BEGIN...END without
dollar-quoting.

This module provides a `split_sql_statements()` function that respects:
- $$ ... $$ dollar-quoted blocks (same as connector)
- Single and double-quoted strings (same as connector)
- -- and /* */ comments (same as connector)
- BEGIN...END block nesting (NEW — the gap this fills)
- DECLARE...BEGIN pattern for anonymous blocks and procedures
"""

import re
from collections.abc import Iterator

# Keywords that precede a scripting BEGIN (not BEGIN TRANSACTION/WORK).
# Validated against Snowflake Scripting documentation:
#   AS    - CREATE PROCEDURE/FUNCTION ... AS BEGIN
#   DO    - FOR ... DO BEGIN ... END; / WHILE ... DO BEGIN ... END;
#   THEN  - IF condition THEN BEGIN ... END;
#   ELSE  - ELSE BEGIN ... END;
#   LOOP  - LOOP BEGIN ... END; END LOOP; (unusual but valid)
_BLOCK_OPENERS = frozenset({"AS", "DO", "THEN", "ELSE", "LOOP"})

# BEGIN TRANSACTION / BEGIN WORK are standalone statements, not block openers.
# Snowflake docs explicitly warn about this ambiguity.
_BEGIN_TRANSACTION_RE = re.compile(r"\bBEGIN\s+(TRANSACTION|WORK)\b", re.IGNORECASE)

# END followed by these keywords closes a compound structure, NOT a BEGIN block.
# These should not decrement begin_depth.
# Full list from Snowflake docs:
#   END IF, END FOR, END LOOP, END WHILE, END CASE, END REPEAT
_COMPOUND_END_RE = re.compile(r"\bEND\s+(IF|LOOP|FOR|WHILE|CASE|REPEAT)\b", re.IGNORECASE)


def split_sql_statements(sql_text: str) -> list[str]:
    """Split SQL text into individual statements, respecting BEGIN...END blocks.

    Returns a list of SQL statement strings (stripped, non-empty).
    """
    return list(_split_iter(sql_text))


def _split_iter(sql_text: str) -> Iterator[str]:
    """Iterate over SQL statements in the input text.

    This is a character-by-character state machine. At any point, the scanner
    is in exactly one state:
      - Normal mode (checking for transitions)
      - Inside a single-quoted string
      - Inside a double-quoted identifier
      - Inside a $$ dollar-quoted block
      - Inside a -- line comment
      - Inside a /* block comment

    In normal mode, it also tracks `begin_depth` — how many BEGIN...END blocks
    we're nested inside. Semicolons only cause a statement split when depth == 0.
    """
    pos = 0
    length = len(sql_text)
    statement_start = 0
    begin_depth = 0
    in_declare_block = False  # Tracks DECLARE...BEGIN pattern

    # State flags — exactly one is True at a time (or all False = normal mode)
    in_single_quote = False
    in_double_quote = False
    in_dollar_quote = False
    in_line_comment = False
    in_block_comment = False

    while pos < length:
        char = sql_text[pos]

        # --- Line comment: skip to end of line ---
        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            pos += 1
            continue

        # --- Block comment: skip to */ ---
        if in_block_comment:
            if char == "*" and pos + 1 < length and sql_text[pos + 1] == "/":
                in_block_comment = False
                pos += 2
            else:
                pos += 1
            continue

        # --- Dollar-quoted block: skip to closing $$ ---
        if in_dollar_quote:
            if char == "$" and pos + 1 < length and sql_text[pos + 1] == "$":
                in_dollar_quote = False
                pos += 2
            else:
                pos += 1
            continue

        # --- Single-quoted string ---
        if in_single_quote:
            if char == "'" and pos + 1 < length and sql_text[pos + 1] == "'":
                pos += 2  # escaped quote ('')
            elif char == "'":
                in_single_quote = False
                pos += 1
            else:
                pos += 1
            continue

        # --- Double-quoted identifier ---
        if in_double_quote:
            if char == '"' and pos + 1 < length and sql_text[pos + 1] == '"':
                pos += 2  # escaped quote ("")
            elif char == '"':
                in_double_quote = False
                pos += 1
            else:
                pos += 1
            continue

        # === Normal mode: detect transitions ===

        # Start of line comment (--)
        if char == "-" and pos + 1 < length and sql_text[pos + 1] == "-":
            in_line_comment = True
            pos += 2
            continue

        # Start of block comment (/*)
        if char == "/" and pos + 1 < length and sql_text[pos + 1] == "*":
            in_block_comment = True
            pos += 2
            continue

        # Start of dollar-quoted block ($$)
        if char == "$" and pos + 1 < length and sql_text[pos + 1] == "$":
            in_dollar_quote = True
            pos += 2
            continue

        # Start of single-quoted string
        if char == "'":
            in_single_quote = True
            pos += 1
            continue

        # Start of double-quoted identifier
        if char == '"':
            in_double_quote = True
            pos += 1
            continue

        # --- Keyword detection (BEGIN / END / DECLARE) ---
        if char.upper() in ("B", "E", "D") and _is_word_boundary(sql_text, pos):
            word = _read_word(sql_text, pos)
            upper_word = word.upper()

            if upper_word == "DECLARE" and _is_word_end(sql_text, pos + 7):
                if _is_declare_block_start(sql_text, pos):
                    in_declare_block = True
                    pos += 7
                    continue

            if upper_word == "BEGIN" and _is_word_end(sql_text, pos + 5):
                if _is_block_begin(sql_text, pos, in_declare_block):
                    begin_depth += 1
                    in_declare_block = False
                    pos += 5
                    continue
                in_declare_block = False  # Reset even if not a block BEGIN

            if upper_word == "END" and _is_word_end(sql_text, pos + 3):
                if begin_depth > 0 and _is_block_end(sql_text, pos):
                    begin_depth -= 1
                    pos += 3
                    continue

        # --- Semicolon: split point only when depth == 0 and not in DECLARE ---
        if char == ";" and begin_depth == 0 and not in_declare_block:
            stmt = sql_text[statement_start : pos + 1].strip()
            if stmt and stmt != ";":
                yield stmt
            statement_start = pos + 1
            pos += 1
            continue

        pos += 1

    # Remaining text after last semicolon
    remainder = sql_text[statement_start:].strip()
    if remainder:
        yield remainder


def _is_word_boundary(text: str, pos: int) -> bool:
    """Check if position is at the start of a word (preceded by non-word char or start)."""
    if pos == 0:
        return True
    prev = text[pos - 1]
    return not (prev.isalnum() or prev == "_")


def _is_word_end(text: str, pos: int) -> bool:
    """Check if position is past the end of a word (followed by non-word char or end)."""
    if pos >= len(text):
        return True
    nxt = text[pos]
    return not (nxt.isalnum() or nxt == "_")


def _read_word(text: str, pos: int) -> str:
    """Read an alphanumeric word starting at pos."""
    end = pos
    while end < len(text) and (text[end].isalnum() or text[end] == "_"):
        end += 1
    return text[pos:end]


def _is_declare_block_start(sql_text: str, declare_pos: int) -> bool:
    """Determine if DECLARE at declare_pos starts a DECLARE...BEGIN block.

    DECLARE starts a block when it appears:
    - After AS (in a procedure/function definition)
    - At the start of a statement (anonymous block)
    """
    preceding_word = _get_preceding_word(sql_text, declare_pos)
    upper_preceding = preceding_word.upper()
    # After AS or at statement start
    return upper_preceding in ("AS", "", ";")


def _is_block_begin(sql_text: str, begin_pos: int, in_declare: bool) -> bool:
    """Determine if a BEGIN at begin_pos is a block opener (not BEGIN TRANSACTION/WORK).

    A BEGIN is a block opener if:
    1. It is NOT followed by TRANSACTION or WORK
    2. One of:
       a. We're inside a DECLARE...BEGIN pattern (in_declare=True)
       b. It IS preceded by AS, THEN, ELSE, or LOOP
       c. It starts an anonymous block (first keyword in statement)
    """
    # Check if it's BEGIN TRANSACTION or BEGIN WORK
    after = sql_text[begin_pos : begin_pos + 30]
    if _BEGIN_TRANSACTION_RE.match(after):
        return False

    # If we're inside a DECLARE block, this BEGIN is definitely the block body
    if in_declare:
        return True

    # Look backwards for the preceding keyword (skip whitespace)
    preceding_word = _get_preceding_word(sql_text, begin_pos)

    if preceding_word.upper() in _BLOCK_OPENERS:
        return True

    # Anonymous block: BEGIN at statement start
    if preceding_word == "" or preceding_word == ";":
        return True

    return False


def _is_block_end(sql_text: str, end_pos: int) -> bool:
    """Determine if END at end_pos closes a BEGIN block (not END IF/LOOP/FOR/WHILE/CASE)."""
    after = sql_text[end_pos : end_pos + 15]
    if _COMPOUND_END_RE.match(after):
        return False
    return True


def _get_preceding_word(text: str, pos: int) -> str:
    """Get the word immediately preceding position pos, skipping whitespace and comments."""
    j = pos - 1
    while True:
        # Skip whitespace
        while j >= 0 and text[j] in (" ", "\t", "\n", "\r"):
            j -= 1
        if j < 0:
            return ""

        # Check if current position is inside a line comment.
        # Find the start of the current line.
        line_start = text.rfind("\n", 0, j + 1) + 1
        line_before_j = text[line_start : j + 1]

        # If there's a -- in this line, check if j is after it
        comment_pos = _find_line_comment_start(line_before_j)
        if comment_pos != -1 and (line_start + comment_pos) <= j:
            # j is inside a comment; skip to just before the --
            j = line_start + comment_pos - 1
            continue

        break

    if j < 0:
        return ""
    # If we hit a semicolon, that's a statement boundary
    if text[j] == ";":
        return ";"
    # Read the word backwards
    end = j + 1
    while j >= 0 and (text[j].isalnum() or text[j] == "_"):
        j -= 1
    return text[j + 1 : end]


def _find_line_comment_start(line: str) -> int:
    """Find the position of -- in a line, ignoring -- inside string literals."""
    in_quote = False
    quote_char = None
    i = 0
    while i < len(line):
        ch = line[i]
        if in_quote:
            if ch == quote_char:
                if i + 1 < len(line) and line[i + 1] == quote_char:
                    i += 2  # escaped quote
                    continue
                in_quote = False
        else:
            if ch in ("'", '"'):
                in_quote = True
                quote_char = ch
            elif ch == "-" and i + 1 < len(line) and line[i + 1] == "-":
                return i
        i += 1
    return -1
