# Schemachange Troubleshooting Guide

This guide covers common errors and their solutions when using schemachange.

**💡 Quick Tip:** Use the [`schemachange verify` command](README.md#verify) to test connectivity and validate your configuration before troubleshooting.

**🙏 Need Help?** For quick answers or to ask questions, check our [GitHub Discussions Q&A](https://github.com/Snowflake-Labs/schemachange/discussions/categories/q-a) - the community can help faster than opening an issue!

---

## Table of Contents

1. [Connection Errors](#connection-errors)
2. [Permission and Access Errors](#permission-and-access-errors)
3. [Security Warnings](#security-warnings)
4. [Configuration and Script Errors](#configuration-and-script-errors)
5. [Migration and Deprecation Warnings (4.1.0+)](#migration-and-deprecation-warnings-410)
6. [Additional Resources](#additional-resources)

---

## Connection Errors

### Error: `250001: Could not connect to Snowflake backend`

**Possible Causes:**
- Incorrect account identifier format
- Network connectivity issues
- Firewall blocking Snowflake endpoints
- Invalid region or cloud provider

**Solutions:**
1. **Test connectivity:** Run `schemachange verify` to diagnose the issue
2. **Check account format:** Should be `<account>.<region>` or `<account>.<region>.<cloud>` (e.g., `myaccount.us-east-1` or `myaccount.us-east-1.aws`)
3. **Verify network access:** Try `ping <account>.<region>.snowflakecomputing.com`
4. **Check firewall rules:** Ensure your firewall allows HTTPS traffic to `*.snowflakecomputing.com`

---

### Error: `Authentication Failed` or `Incorrect username or password`

**Possible Causes:**
- Wrong password or credentials
- MFA enabled but using password instead of PAT
- Expired OAuth token
- Incorrect private key passphrase
- User account is locked or disabled

**Solutions:**
1. **Test credentials:** Run `schemachange verify` to validate your authentication
2. **For MFA-enabled accounts:** Use a Programmatic Access Token (PAT) instead of your password:
   ```bash
   export SNOWFLAKE_PASSWORD="<your_pat_token>"
   schemachange deploy
   ```
3. **Verify authenticator:** Ensure `--snowflake-authenticator` or `SNOWFLAKE_AUTHENTICATOR` matches your authentication method
4. **For JWT authentication:**
   - Verify private key file path is correct
   - Check `SNOWFLAKE_PRIVATE_KEY_FILE_PWD` environment variable (or deprecated `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE`)
   - Ensure the public key is registered with your Snowflake user
5. **For OAuth:** Check that your token file exists and contains a valid, non-expired token
6. See [Authentication](README.md#authentication) and [SECURITY.md](SECURITY.md) for detailed guidance

---

### Error: `unrecognized arguments: --snowflake-private-key-passphrase`

**Cause:** You're using schemachange 4.1.0 or later, which removed this CLI argument for security reasons.

**Solution:** See [Upgrading to 4.1.0](README.md#upgrading-to-410) for complete migration guide. Quick fix:
```bash
export SNOWFLAKE_PRIVATE_KEY_FILE_PWD="my_passphrase"
schemachange deploy --snowflake-authenticator snowflake_jwt \
  --snowflake-private-key-file ~/.ssh/key.p8
```

**⚠️ Note:** `--snowflake-private-key-passphrase` was intentionally removed from CLI in 4.1.0 for security (would be visible in process list). Use environment variable instead.

---

## Permission and Access Errors

### Error: `Change history table does not exist` or `METADATA.SCHEMACHANGE.CHANGE_HISTORY does not exist`

**Possible Causes:**
- First time running schemachange
- Change history table was dropped
- User doesn't have access to the metadata database/schema
- Incorrect change history table name

**Solutions:**
1. **Create the table automatically:** Run with `--create-change-history-table` flag:
   ```bash
   schemachange deploy --create-change-history-table
   ```
2. **Create manually:** See [Change History Table](README.md#change-history-table) for DDL
3. **Check permissions:** Ensure your user has:
   - `CREATE SCHEMA` privilege on the metadata database (if using `--create-change-history-table`)
   - `SELECT` and `INSERT` privileges on the change history table
4. **Verify table name:** Use `-c` or `--schemachange-change-history-table` to specify the correct table

---

### Error: `000606 (57P03): No active warehouse selected in the current session`

**Cause:** No warehouse was specified or the warehouse parameter is not being used properly.

**Symptoms:**
- Error occurs immediately when schemachange tries to query the change history table
- Error message: `No active warehouse selected in the current session. Select an active warehouse with the 'use warehouse' command.`

**Solutions:**

**✅ Fixed in 4.2.0:** This issue is automatically resolved by explicitly setting a warehouse parameter.

1. **Specify warehouse via CLI:**
   ```bash
   schemachange deploy --snowflake-warehouse MY_WAREHOUSE
   # or short form:
   schemachange deploy -w MY_WAREHOUSE
   ```

2. **Set via environment variable:**
   ```bash
   export SNOWFLAKE_WAREHOUSE=MY_WAREHOUSE
   schemachange deploy
   ```

3. **Configure in YAML:**
   ```yaml
   snowflake:
     warehouse: MY_WAREHOUSE
   ```

4. **Set in connections.toml:**
   ```toml
   [myconnection]
   warehouse = "MY_WAREHOUSE"
   ```

**Why warehouse is required:**

While Snowflake allows connecting without a warehouse, schemachange operations **require** an active warehouse for:
- Querying `INFORMATION_SCHEMA.TABLES` (change history lookup)
- Creating change history table
- Executing SQL scripts

**Verify your configuration:**
```bash
schemachange verify
# Look for "default_warehouse" in the output
```

**Note:** In versions before 4.2.0, the warehouse parameter was sometimes ignored due to a bug (see issues [#233](https://github.com/Snowflake-Labs/schemachange/issues/233) and [#235](https://github.com/Snowflake-Labs/schemachange/issues/235)). This is fixed in 4.2.0.

---

### Error: Tasks or anonymous blocks with `BEGIN...END` fail with EOF or parsing errors

**Cause:** The Snowflake connector's `execute_string()` method splits SQL on semicolons, which breaks `BEGIN...END` blocks that aren't protected by delimiters.

**This affects:**
- Tasks with `BEGIN...END` blocks
- Anonymous blocks (stored procedures)
- Any SQL containing multi-statement blocks

**Example that fails:**
```sql
CREATE OR REPLACE TASK my_task
    WAREHOUSE = my_warehouse
    SCHEDULE = '5 minutes'
AS
    BEGIN
        START TRANSACTION;
        SELECT * FROM table1;
        COMMIT;
    END;
```

**Solution:** Use `$$` delimiters to protect the block:

```sql
CREATE OR REPLACE TASK my_task
    WAREHOUSE = my_warehouse
    SCHEDULE = '5 minutes'
AS
$$
BEGIN
    START TRANSACTION;
    SELECT * FROM table1;
    COMMIT;
END;
$$;
```

The `$$` delimiter tells `execute_string()` to treat everything between them as a single statement, preventing it from splitting on internal semicolons.

**Why this happens:** When not using `$$`, the connector sees each semicolon as a statement boundary and tries to execute:
1. `CREATE OR REPLACE TASK... BEGIN START TRANSACTION;`
2. `SELECT * FROM table1;`
3. `COMMIT;`
4. `END;`

Each piece is invalid SQL on its own, causing parsing errors or truncated execution.

**Reference:** [Snowflake CREATE TASK documentation](https://docs.snowflake.com/en/sql-reference/sql/create-task) and [Snowflake Scripting documentation](https://docs.snowflake.com/en/developer-guide/stored-procedure/stored-procedures-snowflake-scripting) both support dollar-quoted (`$$`) syntax.

**Related:** Issues [#253](https://github.com/Snowflake-Labs/schemachange/issues/253) and [#138](https://github.com/Snowflake-Labs/schemachange/issues/138)

---

### Error: `SQL compilation error: Object does not exist` or `Database/Schema does not exist`

**Possible Causes:**
- Database or schema hasn't been created yet
- User doesn't have `USAGE` privilege
- Role doesn't have access to the database/schema
- Typo in database or schema name

**Solutions:**
1. **Create database/schema first:** Run initial setup scripts or create manually
2. **Grant privileges to role:**
   ```sql
   GRANT USAGE ON DATABASE my_database TO ROLE deployment_role;
   GRANT USAGE ON SCHEMA my_database.my_schema TO ROLE deployment_role;
   ```
3. **Verify configuration:** Run `schemachange verify` to see configured database/schema
4. **Check role permissions:** Ensure the role specified in `--snowflake-role` has necessary access

---

## Security Warnings

### Warning: `SECURITY WARNING: connections.toml file has insecure permissions`

**Cause:** Your `connections.toml` file is readable or writable by other users on the system.

**Solution:** Set restrictive permissions (owner read/write only):
```bash
chmod 600 ~/.snowflake/connections.toml
```

Verify the fix:
```bash
ls -l ~/.snowflake/connections.toml
# Should show: -rw------- (600)
```

**Why this matters:** The connections.toml file may contain passwords and tokens. If readable by others, your credentials could be compromised.

---

### Warning: `SECURITY WARNING: Sensitive credentials found in YAML configuration`

**Cause:** Your YAML configuration file contains passwords, tokens, or private key passphrases.

**Solution:** Remove sensitive credentials from YAML and use environment variables or connections.toml instead:

❌ **Don't do this:**
```yaml
snowflake:
  password: "my_password"  # Insecure!
```

✅ **Do this:**
```bash
export SNOWFLAKE_PASSWORD="my_password"
```

**Why this matters:** YAML files are often committed to version control (Git), making credentials visible in repository history. See [SECURITY.md](SECURITY.md) for best practices.

---

## Configuration and Script Errors

### Error: `Failed to render Jinja template` or `TemplateNotFound`

**Possible Causes:**
- Syntax error in Jinja template
- Missing module file
- Incorrect modules folder path

**Solutions:**
1. **Test template rendering:** Use the `render` command to test individual scripts:
   ```bash
   schemachange render path/to/script.sql
   ```
2. **Check modules folder:** Verify `-m` or `--schemachange-modules-folder` points to the correct directory
3. **Verify template syntax:** Check for matching `{% %}` tags, proper variable names, etc.
4. See [Jinja templating engine](README.md#jinja-templating-engine) for details

---

### Error: `Script rendered to empty SQL content` or `Script contains only SQL comments` (Issue #258)

**Root Cause:** After Jinja template processing, the script either:
1. Contains no content (whitespace only)
2. Contains only SQL comments that Snowflake's connector will strip before execution

**Why This Happens:**
When Snowflake connector receives SQL content, it strips comments before execution. If the content becomes empty after stripping, it results in "Empty SQL Statement" error.

**How Schemachange Fixes This:**
- ✅ **Scripts with valid SQL + trailing comments**: Schemachange automatically appends `SELECT 1;` no-op statement to ensure Snowflake has a valid statement to execute. Your metadata comments are preserved.
- ❌ **Comment-only scripts**: Schemachange raises a clear error because these are likely mistakes (placeholder files, TODOs, etc.)

**Common Scenarios:**

1. **All Jinja conditionals evaluate to false:**
   ```sql
   {% if env == 'prod' %}
   CREATE TABLE my_table (id INT);
   {% endif %}
   -- If env != 'prod', this renders to empty content
   ```

2. **File contains only SQL comments (ERROR):**
   ```sql
   -- TODO: Implement this migration later
   -- Placeholder for future changes
   ```
   ❌ This will raise an error - add actual SQL or remove the file.

3. **File contains only whitespace after rendering:**
   ```sql
   {% if feature_enabled %}
   CREATE TABLE my_table (id INT);
   {% endif %}
   -- If feature_enabled is false, only whitespace remains
   ```

4. **File contains only a semicolon after rendering:**
   ```sql
   {% if some_condition %}
   SELECT 1;
   {% endif %}
   ;  -- Trailing semicolon with no SQL above
   ```

5. **Missing or incorrect template variables:**
   ```sql
   {% if feature_flag %}
   CREATE TABLE production_table (id INT);
   {% endif %}
   -- If feature_flag is not provided or is false, content is empty
   ```

**Solutions:**

1. **Test template rendering:** Use the `render` command to see what SQL is actually generated:
   ```bash
   schemachange render path/to/V1.0__my_script.sql
   ```
   This shows the exact SQL content after Jinja processing, including variables used.

2. **Check template variables:** Verify all required variables are provided:
   ```bash
   # Via CLI:
   schemachange deploy -V '{"env": "prod", "feature_flag": true}'

   # Via YAML:
   # schemachange.yaml
   config-vars:
     env: prod
     feature_flag: true

   # Via environment (in CI/CD):
   export SCHEMACHANGE_VARS='{"env": "prod", "feature_flag": true}'
   ```

3. **Add else clauses:** Ensure at least one branch always executes:
   ```sql
   {% if env == 'prod' %}
   CREATE TABLE prod_table (id INT);
   {% else %}
   CREATE TABLE dev_table (id INT);
   {% endif %}
   ```

4. **Check environment differences:** In CI/CD (Azure DevOps, GitHub Actions, etc.), variables might be different than local:
   - Verify environment variables are set correctly in your pipeline
   - Check for typos in variable names (case-sensitive!)
   - Use `schemachange render` locally with the same variables to reproduce the issue

5. **Review the error message:** The error includes helpful debugging info:
   - Raw content preview (first 500 characters)
   - List of all variables provided
   - Specific reasons that can cause empty content

**Example Error Messages:**

**For empty content:**
```
ValueError: Script 'V1.0__my_script.sql' rendered to empty SQL content after Jinja processing.
This can happen when:
  1. The file contains only whitespace
  2. All Jinja conditional blocks evaluate to false
  3. Template variables are missing or incorrect
  4. The file contains only a semicolon after rendering

Raw content preview (first 500 chars):



Provided variables: ['env', 'feature_flag']
```

**For comment-only content:**
```
ValueError: Script 'V1.0__my_script.sql' contains only SQL comments after Jinja processing.
When Snowflake strips comments, this results in an empty SQL statement.

Original content:
-- TODO: Implement this later
-- Placeholder script

Content after comment removal:
''

To fix:
  1. Add actual SQL statements to the script
  2. Remove comment-only scripts from your migrations
  3. If this is a placeholder, add a no-op statement like: SELECT 1; -- placeholder
```

**Note on automatic fix for valid SQL:**
If your script contains valid SQL but ends with comment lines (e.g., metadata), schemachange automatically appends a no-op `SELECT 1;` statement. This ensures Snowflake has a valid statement to execute after stripping comments, while preserving your metadata. You'll see a debug log message when this happens.

**Azure DevOps Specific Tips:**
- Ensure pipeline variables are passed to schemachange command
- Check variable groups and library references
- Verify file encoding (UTF-8 without BOM)
- Check line endings (LF vs CRLF) if using multi-line conditionals

---

### Error: `ValueError: Invalid JSON format` for `--schemachange-vars`

**Cause:** The JSON provided to `--schemachange-vars` or `-V` is malformed.

**Solution:** Ensure proper JSON formatting with double quotes:
```bash
# Correct:
schemachange deploy -V '{"env": "prod", "version": "1.0"}'

# Wrong (single quotes inside):
schemachange deploy -V "{'env': 'prod'}"  # Will fail
```

---

## Migration and Deprecation Warnings (4.1.0+)

### Warning: `Argument '--vars' is deprecated. Use '--schemachange-config-vars' or '-V' instead`

**Cause:** You're using deprecated CLI arguments that were replaced in 4.1.0 with prefixed versions.

**Impact:** Your command still works, but you'll see deprecation warnings. These arguments will be removed in 5.0.0.

**Solution:** Update your commands to use the new parameter names:

```bash
# Old (deprecated, works until 5.0.0):
schemachange deploy --vars '{"env": "prod"}' --log-level INFO --query-tag "deployment"

# New (recommended):
schemachange deploy --schemachange-config-vars '{"env": "prod"}' --schemachange-log-level INFO --snowflake-query-tag "deployment"

# Or use short forms:
schemachange deploy -V '{"env": "prod"}' -L INFO -Q "deployment"
```

**Common Deprecation Mappings:**

| Old (Deprecated) | New (Recommended) | Short Form |
|------------------|-------------------|------------|
| `--vars` | `--schemachange-config-vars` | `-V` |
| `--log-level` | `--schemachange-log-level` | `-L` |
| `--query-tag` | `--snowflake-query-tag` | `-Q` |
| `--verbose` | `-L INFO` or `-L DEBUG` | `-L` |

**See also:** [Migration guide in demo/README.MD](demo/README.MD#-migrating-to-410-new-in-410)

---

### Warning: `Environment variable 'SNOWSQL_PWD' is deprecated. Use 'SNOWFLAKE_PASSWORD' instead`

**Cause:** You're using the deprecated `SNOWSQL_PWD` environment variable.

**Impact:** Still works in 4.x, but will be removed in 5.0.0.

**Solution:** Update your environment variables:

```bash
# Old (deprecated):
export SNOWSQL_PWD="my_password_or_pat"

# New (recommended):
export SNOWFLAKE_PASSWORD="my_password_or_pat"
```

**For CI/CD pipelines:** Update your secret names and variable references in:
- GitHub Actions secrets
- GitLab CI/CD variables
- Jenkins credentials
- Azure DevOps pipeline variables

---

### Error: `TypeError: DeployConfig.__init__() got an unexpected keyword argument 'unknown_key'`

**Cause:** Your YAML configuration file contains keys that schemachange doesn't recognize.

**Impact:**
- In 4.1.0 and earlier: Causes errors
- In 4.2.0+: Shows warnings but continues (backward compatible)

**Solution (if on 4.1.0 or earlier):**

1. **Check for typos** in your YAML config:
   ```yaml
   # Wrong:
   snowflake:
     warehose: MY_WH  # Typo: should be "warehouse"

   # Correct:
   snowflake:
     warehouse: MY_WH
   ```

2. **Remove unknown keys** or check the [Configuration reference](README.md#configuration) for valid parameter names

3. **Upgrade to 4.2.0+** for more forgiving config validation (shows warnings instead of errors)

---

### Issue: Scripts with uppercase `.SQL` extension not being detected

**Status:** ✅ **Not a bug** - schemachange supports case-insensitive file extensions

**If you're experiencing this:**

1. **Verify the filename pattern** matches one of these:
   - `V<version>__<description>.sql` or `.SQL` (versioned)
   - `R__<description>.sql` or `.SQL` (repeatable)
   - `A__<description>.sql` or `.SQL` (always)

2. **Check for proper separators:** Must use **two underscores** (`__`) between prefix and description:
   ```
   ✅ V1.0.0__create_table.SQL     (correct)
   ❌ V1.0.0_create_table.SQL      (wrong - only 1 underscore)
   ❌ V1.0.0___create_table.SQL    (wrong - 3 underscores)
   ```

3. **Test script detection:**
   ```bash
   schemachange deploy --dry-run -L DEBUG
   # Look for "script found" messages in the output
   ```

4. **Verify file system case sensitivity:**
   - On Windows: Usually case-insensitive
   - On Linux: Usually case-sensitive
   - On macOS: Depends on filesystem (APFS can be case-sensitive or insensitive)

**Still having issues?** Please report with:
- Exact filename
- Output from `ls -la` showing the file
- Output from `schemachange deploy --dry-run -L DEBUG`

---

### Warning: `Unknown configuration keys found and will be ignored: <key_names>`

**Cause:** Your YAML configuration contains keys that schemachange doesn't recognize (NEW in 4.2.0).

**Impact:** ⚠️ **Warning only** - schemachange will ignore these keys and continue. This enables:
- **Backward compatibility:** Old deprecated keys won't break your deployment
- **Sideways compatibility:** Tools can add metadata keys without breaking schemachange
- **Typo tolerance:** Typos show warnings instead of halting deployment

**Solution:**

1. **Review the warning** to identify unknown keys
2. **Check for typos** in parameter names
3. **Remove or fix** the unknown keys if they're mistakes
4. **Leave them** if they're intentional metadata for other tools

**Example:**
```yaml
# This YAML has unknown keys but will work in 4.2.0+
schemachange:
  root-folder: ./migrations
  my-custom-metadata: "for my CI tool"  # Unknown, but ignored

snowflake:
  account: myaccount
  warehose: MY_WH  # Typo! Will be ignored (and you'll see a warning)
  warehouse: MY_WH  # Correct - this will be used
```

**Why this change?** Allows different tools in your pipeline to share the same YAML config file without breaking each other.

---

## Additional Resources

- **Test your connection:** Use [`schemachange verify`](README.md#verify) to validate credentials and configuration
- **Enable debug logging:** Run with `-L DEBUG` or `--schemachange-log-level DEBUG` for detailed troubleshooting
- **Security best practices:** See [SECURITY.md](SECURITY.md)
- **Configuration reference:** See [Configuration](README.md#configuration)
- **Authentication methods:** See [Authentication](README.md#authentication)
- **Migration guide:** See [Migrating to 4.1.0+](demo/README.MD#-migrating-to-410-new-in-410)

---

## Still Having Issues?

If you continue to experience problems, check the [GitHub Issues](https://github.com/Snowflake-Labs/schemachange/issues) or open a new issue with:

- The exact error message
- Output from `schemachange verify` (with secrets redacted)
- Your schemachange version: `pip show schemachange`
- Your Python version: `python --version`
- Operating system
- Steps to reproduce the issue

**Tip:** Search existing issues first - your problem may already have a solution!
