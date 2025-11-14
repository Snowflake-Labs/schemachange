# Schemachange Troubleshooting Guide

This guide covers common errors and their solutions when using schemachange.

**💡 Quick Tip:** Use the [`schemachange verify` command](README.md#verify) to test connectivity and validate your configuration before troubleshooting.

---

## Table of Contents

1. [Connection Errors](#connection-errors)
2. [Permission and Access Errors](#permission-and-access-errors)
3. [Security Warnings](#security-warnings)
4. [Configuration and Script Errors](#configuration-and-script-errors)
5. [Additional Resources](#additional-resources)

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
   - Check `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` environment variable
   - Ensure the public key is registered with your Snowflake user
5. **For OAuth:** Check that your token file exists and contains a valid, non-expired token
6. See [Authentication](README.md#authentication) and [SECURITY.md](SECURITY.md) for detailed guidance

---

### Error: `unrecognized arguments: --snowflake-private-key-passphrase`

**Cause:** You're using schemachange 4.1.0 or later, which removed this CLI argument for security reasons.

**Solution:** See [Upgrading to 4.1.0](README.md#upgrading-to-410) for complete migration guide. Quick fix:
```bash
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE="my_passphrase"
schemachange deploy --snowflake-authenticator snowflake_jwt \
  --snowflake-private-key-path ~/.ssh/key.p8
```

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

## Additional Resources

- **Test your connection:** Use [`schemachange verify`](README.md#verify) to validate credentials and configuration
- **Enable debug logging:** Run with `-L DEBUG` or `--schemachange-log-level DEBUG` for detailed troubleshooting
- **Security best practices:** See [SECURITY.md](SECURITY.md)
- **Configuration reference:** See [Configuration](README.md#configuration)
- **Authentication methods:** See [Authentication](README.md#authentication)

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
