# Schemachange Security Best Practices

## Overview

This document provides security guidance for configuring schemachange, with a focus on protecting sensitive credentials and following industry best practices.

---

## ⚠️ Critical Security Warnings

### 1. NEVER Store Passwords in YAML Files

**❌ DON'T DO THIS:**
```yaml
# BAD - Never store passwords in YAML!
config-version: 2

snowflake:
  account: myaccount.us-east-1
  user: my_user
  password: "my_secret_password"  # ❌ INSECURE!
```

**Why?** YAML configuration files are often:
- Committed to version control (Git, SVN, etc.)
- Shared across teams
- Backed up to multiple locations
- Visible in CI/CD logs

### 2. NEVER Use CLI Arguments for Secrets

**❌ DON'T DO THIS:**
```bash
# BAD - CLI arguments are visible in process list and shell history!
schemachange deploy --snowflake-password "my_secret_password"  # ❌ INSECURE!
```

**Why?**
- Visible in `ps` output to all users
- Stored in shell history (`.bash_history`, `.zsh_history`)
- Logged by monitoring tools
- Visible to system administrators

**Note:** schemachange intentionally blocks `--snowflake-private-key-passphrase` via CLI for this reason.

### 3. Secure connections.toml File Permissions

**✅ DO THIS:**
```bash
# Set restrictive permissions on connections.toml
chmod 600 ~/.snowflake/connections.toml

# Verify permissions (should show -rw-------)
ls -l ~/.snowflake/connections.toml
```

**What schemachange checks:**
- Warns if file is readable by group or others
- Warns if file is writable by group or others
- Provides actionable remediation commands

---

## 🔒 Recommended Authentication Methods

⚠️ **IMPORTANT: Snowflake is deprecating password-only authentication. MFA or alternative authentication methods are required for most accounts.**

### Priority Order (Most Secure to Least Secure)

1. **✅ BEST: JWT/Private Key Authentication (Production Automation)**
   - Most secure for automated deployments
   - Key-based authentication
   - No password exposure
   - Recommended by Snowflake for service accounts

   ```bash
   export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
   export SNOWFLAKE_USER="service_account"
   export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
   export SNOWFLAKE_PRIVATE_KEY_PATH="~/.ssh/snowflake_key.p8"
   export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE="key_passphrase"  # Only if key is encrypted
   export SNOWFLAKE_ROLE="DEPLOYMENT_ROLE"
   export SNOWFLAKE_WAREHOUSE="DEPLOYMENT_WH"

   schemachange deploy
   ```

2. **✅ GOOD: Programmatic Access Tokens (PATs) for MFA Accounts**
   - Required for MFA-enabled accounts
   - Token rotation support
   - Better than storing passwords

   ```bash
   export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
   export SNOWFLAKE_USER="my_user"
   export SNOWFLAKE_PASSWORD="<your_pat_token>"  # PAT, not actual password
   export SNOWFLAKE_ROLE="DEPLOYMENT_ROLE"
   export SNOWFLAKE_WAREHOUSE="DEPLOYMENT_WH"

   schemachange deploy
   ```

3. **✅ GOOD: connections.toml (With Proper Permissions)**
   - Centralized credential management
   - Multiple profile support
   - Must have restrictive file permissions (0600)

   ```toml
   # ~/.snowflake/connections.toml (chmod 600)
   [production]
   account = "myaccount.us-east-1"
   user = "deployment_user"
   password = "<pat_token_or_password>"
   role = "DEPLOYMENT_ROLE"
   warehouse = "DEPLOYMENT_WH"
   authenticator = "snowflake"
   ```

4. **✅ ACCEPTABLE: OAuth with Token File**
   - For SSO integration
   - Token file should have restrictive permissions

   ```bash
   export SNOWFLAKE_AUTHENTICATOR="oauth"
   export SNOWFLAKE_TOKEN_FILE_PATH="~/.snowflake/oauth_token.txt"
   chmod 600 ~/.snowflake/oauth_token.txt

   schemachange deploy
   ```

5. **⚠️ USE WITH CAUTION: Password via Environment Variable**
   - Only for development/testing
   - Not suitable for production with MFA
   - Environment variables can leak in logs

   ```bash
   export SNOWFLAKE_PASSWORD="my_password"  # ⚠️ Use PATs instead
   ```

---

## 📊 Parameter Source Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│     Which configuration source should I use?                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Is it a      │
                    │  SECRET?      │
                    │  (password,   │
                    │  token, etc.) │
                    └───────┬───────┘
                            │
                ┌───────────┴───────────┐
                │                       │
             YES│                       │NO
                │                       │
                ▼                       ▼
    ┌───────────────────────┐   ┌─────────────────────┐
    │ Use ENVIRONMENT       │   │ What's the use      │
    │ VARIABLE or           │   │ case?               │
    │ connections.toml      │   └──────────┬──────────┘
    │ (with chmod 600)      │              │
    │                       │              │
    │ ✅ SNOWFLAKE_PASSWORD │    ┌─────────┴─────────┐
    │ ✅ connections.toml   │    │                   │
    │                       │  Same for              Different per
    │ ❌ NEVER CLI          │  all environments      environment
    │ ❌ NEVER YAML         │    │                   │
    └───────────────────────┘    ▼                   ▼
                          ┌──────────────┐   ┌──────────────┐
                          │ Use YAML     │   │ Use CLI args │
                          │ Config File  │   │ or ENV vars  │
                          │              │   │              │
                          │ Examples:    │   │ Examples:    │
                          │ • root-folder│   │ CLI:         │
                          │ • log-level  │   │ -d DATABASE  │
                          │ • vars       │   │              │
                          │              │   │ ENV:         │
                          │ Priority:    │   │ SNOWFLAKE_   │
                          │ CLI > ENV >  │   │ DATABASE     │
                          │ YAML         │   │              │
                          └──────────────┘   └──────────────┘

Legend:
✅ = Recommended
⚠️ = Use with caution
❌ = Never use
```

---

## 🎯 Configuration Priority

Schemachange uses a layered configuration approach:

```
┌──────────────────────────────────────────────────────────┐
│  1. CLI Arguments          (Highest Priority)            │
│     --snowflake-account myaccount                        │
│     Wins in conflicts                                    │
└──────────────────────────────────────────────────────────┘
                            ↓ overrides
┌──────────────────────────────────────────────────────────┐
│  2. Environment Variables                                │
│     SNOWFLAKE_ACCOUNT=myaccount                          │
│     ✅ Best for secrets                                  │
└──────────────────────────────────────────────────────────┘
                            ↓ overrides
┌──────────────────────────────────────────────────────────┐
│  3. YAML Configuration File                              │
│     snowflake.account: myaccount                         │
│     ✅ Best for non-secret settings                      │
└──────────────────────────────────────────────────────────┘
                            ↓ overrides
┌──────────────────────────────────────────────────────────┐
│  4. connections.toml       (Lowest Priority)             │
│     account = "myaccount"                                │
│     ✅ Good for secrets with proper permissions          │
└──────────────────────────────────────────────────────────┘
```

---

## 🔐 Secrets Management by Scenario

### Scenario 1: Local Development

**✅ Recommended Approach:**
```bash
# Use connections.toml for convenience
cat > ~/.snowflake/connections.toml << EOF
[dev]
account = "dev-account.us-east-1"
user = "dev_user"
password = "<your_password_or_pat>"
role = "DEVELOPER"
warehouse = "DEV_WH"
EOF

chmod 600 ~/.snowflake/connections.toml

# Deploy using connection profile
schemachange deploy -C dev
```

**Why?** Convenient for local development, credentials don't leak to version control.

---

### Scenario 2: CI/CD Pipeline (GitHub Actions, Jenkins, etc.)

**✅ Recommended Approach:**
```yaml
# .github/workflows/deploy.yml
- name: Deploy with Schemachange
  env:
    SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
    SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
    SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PAT }}  # PAT recommended
    SNOWFLAKE_ROLE: ${{ secrets.SNOWFLAKE_ROLE }}
    SNOWFLAKE_WAREHOUSE: DEPLOYMENT_WH
    SNOWFLAKE_DATABASE: ${{ matrix.database }}
  run: |
    schemachange deploy --config-folder ./migrations
```

**Why?**
- ✅ Secrets stored in CI/CD secret manager
- ✅ No credentials in code
- ✅ Environment-specific via matrix/variables

---

### Scenario 3: Production Deployment (Automated)

**✅ Recommended Approach - JWT with Service Account:**
```bash
# 1. Generate key pair (one-time setup)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_key.p8 -nocrypt

# 2. Configure Snowflake user with public key
# (Upload public key to Snowflake user)

# 3. Store private key securely
chmod 600 snowflake_key.p8

# 4. Deploy
export SNOWFLAKE_ACCOUNT="prod-account.us-east-1"
export SNOWFLAKE_USER="deployment_service_account"
export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
export SNOWFLAKE_PRIVATE_KEY_PATH="./snowflake_key.p8"

schemachange deploy
```

**Why?**
- ✅ No password needed
- ✅ Key rotation without Snowflake user changes
- ✅ Better audit trail

---

### Scenario 4: Multi-Environment Deployment

**✅ Recommended Approach - YAML + ENV Override:**

**Base Configuration (YAML - Checked into Git):**
```yaml
# config/base-config.yml
config-version: 2

schemachange:
  root-folder: ./migrations
  log-level: INFO
  create-change-history-table: true

snowflake:
  # Non-sensitive defaults
  role: DEPLOYMENT_ROLE
  warehouse: DEPLOYMENT_WH

  # DO NOT include:
  # - account (varies by environment)
  # - user (varies by environment)
  # - password (NEVER in YAML!)
```

**Environment-Specific Configuration (Environment Variables):**
```bash
# Production
export SNOWFLAKE_ACCOUNT="prod-account.us-east-1"
export SNOWFLAKE_USER="prod_deployment"
export SNOWFLAKE_PASSWORD="<prod_pat_token>"
export SNOWFLAKE_DATABASE="PRODUCTION_DB"

schemachange deploy --config-folder ./config

# Staging
export SNOWFLAKE_ACCOUNT="staging-account.us-east-1"
export SNOWFLAKE_USER="staging_deployment"
export SNOWFLAKE_PASSWORD="<staging_pat_token>"
export SNOWFLAKE_DATABASE="STAGING_DB"

schemachange deploy --config-folder ./config
```

---

## 🛡️ Security Checklist

### Before Deployment

- [ ] **No passwords in YAML files** - Check with `grep -r password *.yml`
- [ ] **No passwords in version control** - Use `.gitignore` for sensitive files
- [ ] **connections.toml has 600 permissions** - `ls -l ~/.snowflake/connections.toml`
- [ ] **Private keys have 600 permissions** - `ls -l ~/.ssh/snowflake_key.p8`
- [ ] **Using PATs instead of passwords** - Especially for MFA-enabled accounts
- [ ] **Test with `schemachange verify`** - Before running deploy

### For CI/CD

- [ ] **Secrets in secret manager** - Not in pipeline YAML
- [ ] **Minimal permissions** - Role has only required privileges
- [ ] **Service account** - Not personal accounts
- [ ] **Audit logging enabled** - Track all deployments
- [ ] **Separate environments** - Dev/Staging/Prod isolation

### Regular Maintenance

- [ ] **Rotate credentials quarterly** - PATs, passwords, keys
- [ ] **Review access logs** - Check for unauthorized access
- [ ] **Update dependencies** - Keep schemachange updated
- [ ] **Audit connections.toml** - Remove unused profiles

---

## 🚨 What to Do If Credentials Are Leaked

### If Committed to Version Control:

1. **Immediately rotate the credentials** in Snowflake
2. **Remove from Git history** using `git filter-branch` or BFG Repo-Cleaner
3. **Force push** after cleaning (coordinate with team)
4. **Notify security team** if in production
5. **Review access logs** for unauthorized usage

```bash
# Remove sensitive file from Git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch config-with-secrets.yml" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (after team coordination!)
git push origin --force --all
```

### If Exposed via CLI/Logs:

1. **Rotate credentials immediately**
2. **Clear shell history**: `history -c && history -w`
3. **Clear application logs** containing the credentials
4. **Review who had access** to the system
5. **Implement prevention measures** (use environment variables)

---

## 🔍 Verification and Testing

### Use `schemachange verify` Command

```bash
# Test your configuration and connectivity
schemachange verify

# What it shows:
# ✓ Configuration sources used
# ✓ Masked sensitive parameters (password, tokens)
# ✓ Connection test results
# ✓ Session details after successful connection
```

### Example Output:
```
================================================================================
Schemachange Configuration Verification
================================================================================

Snowflake Connection Configuration:
  Account: myaccount.us-east-1
  User: deployment_user
  Role: DEPLOYMENT_ROLE
  Warehouse: DEPLOYMENT_WH
  Password: ****** (set)

Testing Snowflake Connectivity...
────────────────────────────────────────────────────────────────────────────

✓ Connection Successful!

Connection Details:
  Session ID: 123456789
  Snowflake Version: 8.25.0
```

---

## 📚 Additional Resources

- [Snowflake Key Pair Authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth.html)
- [Snowflake OAuth](https://docs.snowflake.com/en/user-guide/oauth.html)
- [Programmatic Access Tokens (PATs)](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth-use.html#label-pat-workflow)
- [connections.toml Documentation](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect#connecting-using-the-connections-toml-file)

---

## 💡 Quick Reference

| Credential Type | CLI | ENV | YAML | connections.toml | Recommended |
|-----------------|-----|-----|------|------------------|-------------|
| Password/PAT | ❌ | ✅ | ❌ | ✅ (chmod 600) | ENV or connections.toml |
| Private Key Passphrase | ❌ | ✅ | ❌ | ✅ (chmod 600) | ENV or connections.toml |
| OAuth Token | ❌ | ❌ | ❌ | Use token-file-path | Token file |
| Account | ✅ | ✅ | ✅ | ✅ | YAML or ENV |
| User | ✅ | ✅ | ✅ | ✅ | YAML or ENV |
| Role | ✅ | ✅ | ✅ | ✅ | YAML |
| Warehouse | ✅ | ✅ | ✅ | ✅ | YAML |
| Database | ✅ | ✅ | ✅ | ✅ | ENV or CLI |

---

**Remember: Security is not a feature, it's a requirement!** 🔒
