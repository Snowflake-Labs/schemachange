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

⚠️ **SNOWFLAKE AUTHENTICATION REQUIREMENTS (2024-2025):**

- **Service users:** Password authentication is **NOT SUPPORTED**. Must use PAT, Key Pair (JWT), OAuth, or WIF.
- **Human users (CLI/CI/CD):** **PREFERRED** to use PAT, Key Pair (JWT), or OAuth. Password+MFA is allowed but not recommended for automation.
- **Human users (Interactive):** Password+MFA is acceptable for interactive sessions but use PAT/Key Pair for automation.

### Priority Order (Most Secure to Least Secure)

1. **✅ BEST: JWT/Private Key Authentication (Service Accounts & Automation)**
   - **REQUIRED** for service accounts (password not supported)
   - **PREFERRED** for all automation (human or service accounts)
   - Most secure - no password exposure
   - Key-based authentication

   ```bash
   export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
   export SNOWFLAKE_USER="service_account"
   export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
   export SNOWFLAKE_PRIVATE_KEY_FILE="~/.ssh/snowflake_key.p8"
   export SNOWFLAKE_PRIVATE_KEY_FILE_PWD="key_passphrase"  # Only if key is encrypted
   export SNOWFLAKE_ROLE="DEPLOYMENT_ROLE"
   export SNOWFLAKE_WAREHOUSE="DEPLOYMENT_WH"

   schemachange deploy
   ```

2. **✅ PREFERRED for Automation: Programmatic Access Tokens (PATs)**
   - **PREFERRED** for human users in CLI/CI/CD scenarios
   - Supported for service users (alternative to JWT)
   - Token rotation support
   - Bypasses MFA prompts for automation

   ```bash
   export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
   export SNOWFLAKE_USER="human_user"
   export SNOWFLAKE_PASSWORD="<your_pat_token>"  # PAT token, NOT your login password
   export SNOWFLAKE_ROLE="DEPLOYMENT_ROLE"
   export SNOWFLAKE_WAREHOUSE="DEPLOYMENT_WH"

   schemachange deploy
   ```

3. **✅ GOOD: connections.toml (With Proper Permissions)**
   - Centralized credential management
   - Multiple profile support
   - **Must have restrictive file permissions (0600)**
   - Use PAT tokens for human users, JWT for service accounts

   ```toml
   # ~/.snowflake/connections.toml (chmod 600)
   [production]
   account = "myaccount.us-east-1"
   user = "service_account"
   authenticator = "snowflake_jwt"
   private_key_file = "~/.ssh/snowflake_key.p8"
   # private_key_file_pwd = "passphrase"  # Only if key is encrypted
   role = "DEPLOYMENT_ROLE"
   warehouse = "DEPLOYMENT_WH"
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

5. **⚠️ NOT RECOMMENDED for Automation: Password + MFA**
   - **NOT SUPPORTED** for service accounts
   - Allowed for human users in interactive sessions
   - **NOT RECOMMENDED** for CLI/CI/CD automation (requires manual MFA input)
   - Use PAT or Key Pair instead for automation

   ```bash
   # ⚠️ Works for human users but requires MFA prompts (not suitable for automation)
   export SNOWFLAKE_PASSWORD="my_login_password"
   schemachange deploy  # Will prompt for MFA (blocks automation)
   ```

6. **❌ DEPRECATED: Password-Only (No MFA)**
   - **NOT SUPPORTED** - Snowflake requires MFA for password authentication
   - Use PAT, Key Pair, or OAuth instead

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

**✅ Recommended Approach - Human User with MFA:**
```bash
# Use connections.toml with PAT token
cat > ~/.snowflake/connections.toml << EOF
[dev]
account = "dev-account.us-east-1"
user = "dev_user"
password = "<your_pat_token>"  # PAT token, NOT your login password
role = "DEVELOPER"
warehouse = "DEV_WH"
EOF

chmod 600 ~/.snowflake/connections.toml

# Deploy using connection profile
schemachange deploy -C dev
```

**Why?**
- ✅ Convenient for local development
- ✅ Credentials don't leak to version control
- ✅ No MFA prompts during deployment (unlike password+MFA)

**How to get a PAT:**
1. Log into Snowflake UI
2. Go to user preferences
3. Generate new Programmatic Access Token
4. Copy and use in place of password

**Alternative - Password+MFA (Not Recommended for Automation):**
```bash
# ⚠️ Acceptable for interactive sessions but will prompt for MFA
export SNOWFLAKE_PASSWORD="my_login_password"
schemachange deploy -C dev  # Will prompt for MFA code each time
```

---

### Scenario 2: CI/CD Pipeline (GitHub Actions, Jenkins, etc.)

**✅ BEST: JWT with Service Account (Recommended):**
```yaml
# .github/workflows/deploy.yml
- name: Deploy with Schemachange
  env:
    SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
    SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_SERVICE_ACCOUNT }}  # Service account
    SNOWFLAKE_AUTHENTICATOR: "snowflake_jwt"
    SNOWFLAKE_PRIVATE_KEY_FILE: ${{ secrets.SNOWFLAKE_PRIVATE_KEY_FILE }}
    SNOWFLAKE_PRIVATE_KEY_FILE_PWD: ${{ secrets.SNOWFLAKE_KEY_PASSPHRASE }}
    SNOWFLAKE_ROLE: DEPLOYMENT_ROLE
    SNOWFLAKE_WAREHOUSE: DEPLOYMENT_WH
    SNOWFLAKE_DATABASE: ${{ matrix.database }}
  run: |
    # Write private key to temp file
    echo "${{ secrets.SNOWFLAKE_PRIVATE_KEY }}" > /tmp/snowflake_key.p8
    chmod 600 /tmp/snowflake_key.p8

    schemachange deploy --config-folder ./migrations

    # Clean up
    rm -f /tmp/snowflake_key.p8
```

**Alternative - PAT with Human Account (Less Preferred):**
```yaml
- name: Deploy with Schemachange
  env:
    SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
    SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
    SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PAT }}  # PAT token
    SNOWFLAKE_ROLE: DEPLOYMENT_ROLE
    SNOWFLAKE_WAREHOUSE: DEPLOYMENT_WH
  run: |
    schemachange deploy --config-folder ./migrations
```

**Why JWT or PAT for automation:**
- ✅ **Service accounts cannot use passwords** - JWT or PAT required
- ✅ **Human accounts (automation)** - JWT or PAT preferred (no MFA prompts)
- ✅ More secure - no password exposure, better audit trail
- ✅ Key rotation without Snowflake user changes (JWT) or token rotation (PAT)

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
export SNOWFLAKE_PRIVATE_KEY_FILE="./snowflake_key.p8"

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

**Option 1 - JWT with Service Account (Recommended):**
```bash
# Production
export SNOWFLAKE_ACCOUNT="prod-account.us-east-1"
export SNOWFLAKE_USER="prod_service_account"
export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
export SNOWFLAKE_PRIVATE_KEY_FILE="~/.ssh/snowflake_prod.p8"
export SNOWFLAKE_DATABASE="PRODUCTION_DB"

schemachange deploy --config-folder ./config

# Staging
export SNOWFLAKE_ACCOUNT="staging-account.us-east-1"
export SNOWFLAKE_USER="staging_service_account"
export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
export SNOWFLAKE_PRIVATE_KEY_FILE="~/.ssh/snowflake_staging.p8"
export SNOWFLAKE_DATABASE="STAGING_DB"

schemachange deploy --config-folder ./config
```

**Option 2 - PAT with Human Account:**
```bash
# Production
export SNOWFLAKE_ACCOUNT="prod-account.us-east-1"
export SNOWFLAKE_USER="prod_deployment"
export SNOWFLAKE_PASSWORD="<prod_pat_token>"  # PAT, not password
export SNOWFLAKE_DATABASE="PRODUCTION_DB"

schemachange deploy --config-folder ./config
```

---

## 🛡️ Security Checklist

### Before Deployment

- [ ] **No passwords/secrets in YAML files** - Check with `grep -r password *.yml`
- [ ] **No passwords/secrets in version control** - Use `.gitignore` for sensitive files
- [ ] **connections.toml has 600 permissions** - `ls -l ~/.snowflake/connections.toml`
- [ ] **Private keys have 600 permissions** - `ls -l ~/.ssh/snowflake_key.p8`
- [ ] **Using JWT or PAT for service accounts** - Password auth is not supported
- [ ] **Using JWT or PAT for automation** - Preferred over password+MFA (no interactive prompts)
- [ ] **Test with `schemachange verify`** - Before running deploy

### For CI/CD

- [ ] **Secrets in secret manager** - Not in pipeline YAML
- [ ] **Using JWT or PAT** - Preferred (passwords not supported for service accounts, not recommended for human users)
- [ ] **Minimal permissions** - Role has only required privileges
- [ ] **Service account preferred** - Or use PAT/JWT with human account (avoid password+MFA for automation)
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

### Authentication Method by Use Case

| Use Case | Recommended Method | Why |
|----------|-------------------|-----|
| **Service Accounts** | JWT (private key) or PAT | ✅ **REQUIRED** - passwords not supported |
| **CI/CD Automation** | JWT (private key) or PAT | ✅ **PREFERRED** - no interactive MFA prompts |
| **Human Users (Automation)** | PAT or JWT | ✅ **PREFERRED** - bypasses MFA prompts |
| **Human Users (Interactive)** | Password+MFA or PAT | ⚠️ Password+MFA allowed but PAT preferred |
| **Local Development** | PAT via connections.toml | ✅ Convenient + no MFA prompts |
| **Legacy (Unsupported)** | Password-only (no MFA) | ❌ **BLOCKED** by Snowflake |

### Parameter Source Recommendations

| Credential Type | CLI | ENV | YAML | connections.toml | Recommended |
|-----------------|-----|-----|------|------------------|-------------|
| PAT Token | ❌ | ✅ | ❌ | ✅ (chmod 600) | ENV or connections.toml |
| Private Key File (`private_key_file`) | ❌ | ✅ | ❌ | ✅ (chmod 600) | ENV or connections.toml |
| Private Key Password (`private_key_file_pwd`) | ❌ | ✅ | ❌ | ✅ (chmod 600) | ENV or connections.toml |
| OAuth Token | ❌ | ❌ | ❌ | Use token-file-path | Token file |
| Account | ✅ | ✅ | ✅ | ✅ | YAML or ENV |
| User | ✅ | ✅ | ✅ | ✅ | YAML or ENV |
| Role | ✅ | ✅ | ✅ | ✅ | YAML |
| Warehouse | ✅ | ✅ | ✅ | ✅ | YAML |
| Database | ✅ | ✅ | ✅ | ✅ | ENV or CLI |

---

**Remember: Security is not a feature, it's a requirement!** 🔒
