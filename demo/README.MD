# Schemachange Demos

Get hands-on with schemachange! Three practical demos show you how database change management works in real-world scenarios.

## 🚀 Quick Start

**Want to see schemachange in action in 5 minutes?**

### 1. Choose Your Demo

| Demo | What It Shows | Best For |
|------|--------------|----------|
| [basics_demo](basics_demo/) | Core functionality - create tables, views, basic migrations | First-time users, learning the basics |
| [citibike_demo](citibike_demo/) | Real-world data pipeline - loading and transforming data | Understanding practical use cases |
| [citibike_demo_jinja](citibike_demo_jinja/) | Advanced templating with Jinja macros | Power users, complex workflows |

### 2. Set Up Your Snowflake Environment

**You'll need:**
- ✅ A Snowflake account (free trial works great!)
- ✅ A database and warehouse (we'll help you create these)
- ✅ Credentials with deployment privileges

**Quick setup:**
1. Run [initialize.sql](provision/initialize.sql) - Creates database, warehouse, and roles
2. Run [setup_schemachange_schema.sql](provision/setup_schemachange_schema.sql) - Creates the change tracking schema

### 3. Authenticate

Choose your authentication method:

**🔐 For local testing (recommended for first-timers):**
```bash
# Use connections.toml for convenience
cat > ~/.snowflake/connections.toml << EOF
[demo]
account = "myaccount.us-east-1"
user = "my_user"
password = "my_password_or_pat"
role = "SCHEMACHANGE_DEMO-DEPLOY"
warehouse = "SCHEMACHANGE_DEMO_WH"
database = "SCHEMACHANGE_DEMO"
EOF

chmod 600 ~/.snowflake/connections.toml
schemachange deploy -C demo --config-folder ./demo/basics_demo
```

**🤖 For CI/CD (recommended for automation):**
```bash
# Use environment variables (keeps secrets out of version control)
# NOTE: Using SNOWFLAKE_* environment variables (NEW in 4.1.0)
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="service_account"
export SNOWFLAKE_PASSWORD="<your_pat_token>"  # Use a PAT for MFA accounts
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

schemachange deploy --config-folder ./demo/basics_demo
```

**Alternative: Using CLI arguments (NEW in 4.1.0)**
```bash
# Using new --snowflake-* prefixed parameters
schemachange deploy \
  --config-folder ./demo/basics_demo \
  --snowflake-account "myaccount.us-east-1" \
  --snowflake-user "service_account" \
  --snowflake-password "${SNOWFLAKE_PASSWORD}" \
  --snowflake-role "SCHEMACHANGE_DEMO-DEPLOY" \
  --snowflake-warehouse "SCHEMACHANGE_DEMO_WH" \
  --snowflake-database "SCHEMACHANGE_DEMO"
```

**⚠️ Deprecated (still works until 5.0.0):**
```bash
# Old -a/-u/-r/-w/-d short forms (deprecated)
schemachange deploy --config-folder ./demo/basics_demo \
  -a "myaccount.us-east-1" \
  -u "service_account" \
  -r "SCHEMACHANGE_DEMO-DEPLOY" \
  -w "SCHEMACHANGE_DEMO_WH" \
  -d "SCHEMACHANGE_DEMO"
# ⚠️ Shows deprecation warnings. See migration guide below.
```

**📚 More authentication methods?** See examples below or the [Authentication Guide](../README.md#authentication).

**🔄 Using deprecated parameters?** See the [Migration Guide](#-migrating-to-410-new-in-410) below for parameter mapping.

---

### 🔐 Advanced Authentication Methods (NEW in 4.1.0)

**Choose the right authentication for your use case:**

#### JWT (Private Key) - Best for Service Accounts

**Use when:** CI/CD, service accounts, highest security

```bash
# 1. Generate key pair (one-time setup)
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 des3 -inform PEM -out rsa_key.p8
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# 2. Register public key in Snowflake
ALTER USER service_account SET RSA_PUBLIC_KEY='<contents_of_rsa_key.pub>';

# 3. Run schemachange with JWT (using ENV variables)
# NOTE: SNOWFLAKE_* and authentication params are NEW in 4.1.0
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="service_account"
export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
export SNOWFLAKE_PRIVATE_KEY_FILE="~/.ssh/rsa_key.p8"
export SNOWFLAKE_PRIVATE_KEY_FILE_PWD="your_passphrase"
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

schemachange deploy --config-folder ./demo/basics_demo
```

**Alternative: Using CLI arguments (NEW in 4.1.0)**
```bash
# CLI authentication parameters are NEW in 4.1.0
# Note: Passphrase must be in ENV for security (not visible in process list)
export SNOWFLAKE_PRIVATE_KEY_FILE_PWD="your_passphrase"

schemachange deploy \
  --config-folder ./demo/basics_demo \
  --snowflake-account "myaccount.us-east-1" \
  --snowflake-user "service_account" \
  --snowflake-authenticator "snowflake_jwt" \
  --snowflake-private-key-file "~/.ssh/rsa_key.p8" \
  --snowflake-role "SCHEMACHANGE_DEMO-DEPLOY" \
  --snowflake-warehouse "SCHEMACHANGE_DEMO_WH" \
  --snowflake-database "SCHEMACHANGE_DEMO"
```

**Alternative: connections.toml with JWT**

```toml
# ~/.snowflake/connections.toml
[demo_jwt]
account = "myaccount.us-east-1"
user = "service_account"
authenticator = "snowflake_jwt"
private_key_file = "~/.ssh/rsa_key.p8"
role = "SCHEMACHANGE_DEMO-DEPLOY"
warehouse = "SCHEMACHANGE_DEMO_WH"
database = "SCHEMACHANGE_DEMO"
```

```bash
# Passphrase must be in ENV (not in connections.toml for security)
export SNOWFLAKE_PRIVATE_KEY_FILE_PWD="your_passphrase"
schemachange deploy -C demo_jwt --config-folder ./demo/basics_demo
```

**⚠️ Deprecated (still works until 5.0.0):**
```bash
# Using old parameter names (deprecated)
export SNOWFLAKE_PRIVATE_KEY_PATH="~/.ssh/rsa_key.p8"  # ⚠️ Use SNOWFLAKE_PRIVATE_KEY_FILE
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE="your_passphrase"  # ⚠️ Use SNOWFLAKE_PRIVATE_KEY_FILE_PWD
# Shows deprecation warnings
```

---

#### External Browser / SSO - Best for Interactive Use

**Use when:** Local development, MFA enabled, SSO/Okta

```bash
# Opens browser for authentication
# NOTE: SNOWFLAKE_* environment variables are NEW in 4.1.0
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="my_user"
export SNOWFLAKE_AUTHENTICATOR="externalbrowser"
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

schemachange deploy --config-folder ./demo/basics_demo
```

**Alternative: Using CLI arguments (NEW in 4.1.0)**
```bash
schemachange deploy \
  --config-folder ./demo/basics_demo \
  --snowflake-account "myaccount.us-east-1" \
  --snowflake-user "my_user" \
  --snowflake-authenticator "externalbrowser" \
  --snowflake-role "SCHEMACHANGE_DEMO-DEPLOY" \
  --snowflake-warehouse "SCHEMACHANGE_DEMO_WH" \
  --snowflake-database "SCHEMACHANGE_DEMO"
```

Browser will open automatically for authentication. Works with MFA, Okta, and other SSO providers.

---

#### OAuth Token - For Platform Integrations

**Use when:** Integrating with platforms that provide OAuth tokens

```bash
# 1. Get OAuth token from your platform and save it
echo "your_oauth_token" > ~/.snowflake/oauth_token.txt
chmod 600 ~/.snowflake/oauth_token.txt

# 2. Run schemachange with OAuth (using ENV variables)
# NOTE: SNOWFLAKE_* and authentication params are NEW in 4.1.0
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="my_user"
export SNOWFLAKE_AUTHENTICATOR="oauth"
export SNOWFLAKE_TOKEN_FILE_PATH="~/.snowflake/oauth_token.txt"
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

schemachange deploy --config-folder ./demo/basics_demo
```

**Alternative: Using CLI arguments (NEW in 4.1.0)**
```bash
schemachange deploy \
  --config-folder ./demo/basics_demo \
  --snowflake-account "myaccount.us-east-1" \
  --snowflake-user "my_user" \
  --snowflake-authenticator "oauth" \
  --snowflake-token-file-path "~/.snowflake/oauth_token.txt" \
  --snowflake-role "SCHEMACHANGE_DEMO-DEPLOY" \
  --snowflake-warehouse "SCHEMACHANGE_DEMO_WH" \
  --snowflake-database "SCHEMACHANGE_DEMO"
```

---

#### Programmatic Access Token (PAT) - For MFA Accounts

**Use when:** MFA enabled, CI/CD

```bash
# Generate PAT in Snowflake UI: User Preferences → Password → Generate Token
# NOTE: SNOWFLAKE_* environment variables are NEW in 4.1.0
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="my_user"
export SNOWFLAKE_PASSWORD="<your_pat_token>"  # PAT, not password!
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

schemachange deploy --config-folder ./demo/basics_demo
```

**Alternative: Using CLI arguments (NEW in 4.1.0)**
```bash
schemachange deploy \
  --config-folder ./demo/basics_demo \
  --snowflake-account "myaccount.us-east-1" \
  --snowflake-user "my_user" \
  --snowflake-password "${SNOWFLAKE_PASSWORD}" \
  --snowflake-role "SCHEMACHANGE_DEMO-DEPLOY" \
  --snowflake-warehouse "SCHEMACHANGE_DEMO_WH" \
  --snowflake-database "SCHEMACHANGE_DEMO"
```

**⚠️ Deprecated (still works until 5.0.0):**
```bash
# Using old -a/-u/-r/-w/-d short forms (deprecated)
export SNOWSQL_PWD="<your_pat_token>"  # ⚠️ SNOWSQL_PWD is deprecated, use SNOWFLAKE_PASSWORD

schemachange deploy --config-folder ./demo/basics_demo \
  -a "myaccount.us-east-1" \
  -u "my_user" \
  -r "SCHEMACHANGE_DEMO-DEPLOY" \
  -w "SCHEMACHANGE_DEMO_WH" \
  -d "SCHEMACHANGE_DEMO"
# ⚠️ Shows deprecation warnings. See migration guide below.
```

**💡 Tip:** Use `schemachange verify` to test your authentication before running deploy!

---

### 4. Run Your First Demo

```bash
# If using connections.toml:
schemachange deploy -C demo --config-folder ./demo/basics_demo

# If using environment variables:
schemachange deploy --config-folder ./demo/basics_demo
```

**🎉 Success!** You should see:
- ✅ Connection established
- ✅ Change history table created
- ✅ Migration scripts executed
- ✅ Changes logged

**What happened?** Schemachange read your migration scripts in order, executed them against Snowflake, and tracked which changes were applied in a change history table.

---

## 💡 Who Is This For?

### 🧪 Trying Schemachange? (Evaluators & Users)

**You want to:**
- See schemachange in action before adopting it
- Learn how database change management works
- Get working examples for your team
- Understand the workflow

**→ Start with:** [Quick Start](#quick-start) above, then explore [Demo Details](#demo-details) below

---

### 🔧 Contributing to Schemachange? (Developers)

**You want to:**
- Test your bug fix or feature against a real Snowflake account
- Run CI/CD tests locally before submitting a PR
- Ensure your changes don't break existing functionality

**→ Jump to:** [Contributor Setup](#contributor-setup) below

## 📚 Demo Details

### basics_demo

**What you'll learn:**
- How to create and version database objects (tables, views)
- Basic migration script naming conventions
- Change history tracking

**Key scripts:**
- `V1.0.0__initial_setup.sql` - Creates first tables
- `V1.0.1__add_columns.sql` - Demonstrates schema evolution
- `R__view.sql` - Repeatable script (runs every time)

**Run it:**
```bash
schemachange deploy --config-folder ./demo/basics_demo
```

---

### citibike_demo

**What you'll learn:**
- Real-world data pipeline setup
- Loading external data from S3
- Creating stages and file formats
- Data transformation workflows

**Based on:** NYC Citi Bike open dataset

**Run it:**
```bash
schemachange deploy --config-folder ./demo/citibike_demo
```

---

### citibike_demo_jinja

**What you'll learn:**
- Jinja templating for reusable SQL
- Macro creation and usage
- Dynamic SQL generation
- Complex deployment patterns

**Extends:** citibike_demo with advanced templating

**Run it:**
```bash
schemachange deploy --config-folder ./demo/citibike_demo_jinja
```

## 🔧 Contributor Setup

**Contributing to schemachange?** Test your changes locally before submitting a PR!

### Prerequisites

1. **Fork the repository** and clone it locally
2. **Run the provision scripts** to set up your test environment:
   ```bash
   # Run these in Snowflake (via Snowflake CLI, Snowsight, or any SQL client)
   # 1. Creates database, warehouse, and roles
   cd provision
   snow sql -f initialize.sql

   # 2. Creates the SCHEMACHANGE schema for tracking
   snow sql -f setup_schemachange_schema.sql
   ```

3. **Set up authentication** (see [Quick Start - Step 3](#3-authenticate) above or the [Authentication Guide](../README.md#authentication) for more options)

### Running Tests Locally

```bash
# Test your changes against basics_demo
export SNOWFLAKE_ACCOUNT="myaccount"
export SNOWFLAKE_USER="my_user"
export SNOWFLAKE_PASSWORD="<your_password_or_pat>"
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

# Run a demo to test your code
python -m schemachange deploy --config-folder ./demo/basics_demo
```

### GitHub Actions Setup

**To run CI/CD tests in your fork:**

1. **Navigate to:** Your Fork → Settings → Secrets and Variables → Actions
2. **Add these secrets:**
   - `SCHEMACHANGE_SNOWFLAKE_ACCOUNT` - Your Snowflake account identifier
   - `SCHEMACHANGE_SNOWFLAKE_USER` - Service account username
   - `SCHEMACHANGE_SNOWFLAKE_PASSWORD` - Service account password or PAT

3. **Push your branch** - GitHub Actions will automatically run the demo tests

**What the CI/CD tests do:**
- ✅ Run setup scripts to create temporary test schemas
- ✅ Execute all three demos (basics, citibike, citibike_jinja)
- ✅ Verify your changes don't break existing functionality
- ✅ Run teardown scripts to clean up

---

## 🔄 Migrating to 4.1.0+ (NEW in 4.1.0)

**Upgrading from 4.0.x?** The 4.1.0 release introduced new prefixed parameter naming for better clarity and consistency. Your existing configurations will continue to work (deprecated parameters supported until 5.0.0), but you'll see deprecation warnings.

### Quick Migration Reference

**Deprecated (works until 5.0.0) → New (recommended)**

| Category | Old Parameter | New Parameter | Notes |
|----------|---------------|---------------|-------|
| **CLI Arguments** | `--vars` | `--schemachange-config-vars` | Config vars for Jinja |
| | `--log-level` | `--schemachange-log-level` or `-L` | Logging verbosity |
| | `--verbose` | `-L INFO` or `-L DEBUG` | Deprecated flag |
| | `--query-tag` | `--snowflake-query-tag` | Snowflake query tagging |
| **Environment Variables** | `SNOWSQL_PWD` | `SNOWFLAKE_PASSWORD` | Password or PAT |

**NEW in 4.1.0 - Authentication CLI Support:**
- `--snowflake-password`, `--snowflake-authenticator`, `--snowflake-private-key-path`
- Previously only available via ENV or YAML, now available on CLI too!

### Version Pinning Strategy

**Want to control your upgrade path?**

```bash
# Pin to 4.1.x series (get bug fixes, avoid breaking changes)
pip install "schemachange>=4.1.0,<4.2.0"

# Pin to 4.x series (stay on 4.x, avoid 5.0.0 breaking changes)
pip install "schemachange>=4.1.0,<5.0.0"

# Always get latest (not recommended for production)
pip install schemachange --upgrade
```

**Recommended for production:** Pin to minor version and test upgrades in non-production first.

### Parameter Style Examples

**🟢 Current Best Practice (4.1.0+)**

```bash
# CLI with new prefixed arguments
schemachange deploy \
  --config-folder ./demo/basics_demo \
  --schemachange-config-vars '{"env": "prod"}' \
  --schemachange-log-level INFO \
  --snowflake-account "myaccount" \
  --snowflake-user "deploy_user" \
  --snowflake-password "${SNOWFLAKE_PASSWORD}" \
  --snowflake-role "DEPLOY_ROLE" \
  --snowflake-warehouse "DEPLOY_WH" \
  --snowflake-database "PROD_DB"
```

**🟡 Legacy Style (still works, shows warnings)**

```bash
# Old unprefixed arguments (deprecated)
schemachange deploy \
  --config-folder ./demo/basics_demo \
  --vars '{"env": "prod"}' \
  --log-level INFO \
  -a "myaccount" \
  -u "deploy_user" \
  -r "DEPLOY_ROLE" \
  -w "DEPLOY_WH" \
  -d "PROD_DB"
```

### Configuration Priority Order

**Understanding precedence (highest to lowest):**

```
CLI Arguments > Environment Variables > YAML Config > connections.toml
```

**Example - How priority works:**

```bash
# connections.toml
[prod]
database = "PROD_DB"
warehouse = "SMALL_WH"

# ENV variable overrides connections.toml
export SNOWFLAKE_WAREHOUSE="LARGE_WH"

# CLI overrides both ENV and connections.toml
schemachange deploy \
  -C prod \
  --snowflake-database "TEST_DB"

# Result: database=TEST_DB, warehouse=LARGE_WH
```

### Testing Different Parameter Styles

**Want to verify backward compatibility?**

```python
# Test 1: New prefixed style (recommended)
import subprocess

result = subprocess.run([
    "schemachange", "deploy",
    "--config-folder", "./demo/basics_demo",
    "--schemachange-config-vars", '{"env": "test"}',
    "--snowflake-account", "myaccount"
], capture_output=True, text=True)

# Test 2: Legacy style (should show warnings but work)
result = subprocess.run([
    "schemachange", "deploy",
    "--config-folder", "./demo/basics_demo",
    "--vars", '{"env": "test"}',
    "-a", "myaccount"
], capture_output=True, text=True)

# Check for deprecation warnings
assert "deprecated" in result.stderr.lower()
```

### YAML Config Version 2 (NEW in 4.1.0)

**New structured format with separate sections:**

```yaml
# schemachange.yml (v2 format)
schemachange:
  root-folder: ./migrations
  config-vars:
    env: production
  log-level: INFO

snowflake:
  account: myaccount
  user: deploy_user
  role: DEPLOY_ROLE
  warehouse: DEPLOY_WH
  database: PROD_DB
```

**Legacy flat format (still supported):**

```yaml
# schemachange.yml (v1 format)
root-folder: ./migrations
config-vars:
  env: production
log-level: INFO
snowflake-account: myaccount
snowflake-user: deploy_user
snowflake-role: DEPLOY_ROLE
```

### Migration Checklist

**Migrating to 4.1.0+ parameter style:**

- [ ] **Read the deprecation warnings** in your logs
- [ ] **Test in non-production first** with new parameter style
- [ ] **Update CLI scripts** to use `--schemachange-*` and `--snowflake-*` prefixes
- [ ] **Update ENV variables** from `SNOWSQL_PWD` to `SNOWFLAKE_PASSWORD`
- [ ] **Consider YAML v2 format** for new projects (both formats supported)
- [ ] **Pin your version** in `requirements.txt` or `pyproject.toml`
- [ ] **Plan 5.0.0 migration** before the 12-month deprecation period ends

**Need help?** See [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) or [open an issue](https://github.com/Snowflake-Labs/schemachange/issues)

---

## 📖 Additional Resources

**Need more help?**
- 📘 [Main README](../README.md) - Complete schemachange documentation
- 🔐 [Authentication Guide](../README.md#authentication) - JWT, PAT, SSO, and all authentication methods
- 🔧 [Configuration Guide](../README.md#configuration) - connections.toml, YAML, ENV variables, and precedence rules
- 🛡️ [SECURITY.md](../SECURITY.md) - Security best practices for credential management
- 🐛 [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Common issues and solutions
- 🤝 [CONTRIBUTING.md](../.github/CONTRIBUTING.md) - How to contribute to schemachange
- 🌐 [GitHub Issues](https://github.com/Snowflake-Labs/schemachange/issues) - Report bugs or request features

**Quick references from main README:**
- [Environment Variables](../README.md#environment-variables) - Complete ENV variable reference
- [Configuration Priority](../README.md#configuration-priority) - Understanding the precedence chain
- [CLI Arguments](../README.md#commands) - All command-line options
- [Session Parameters](../README.md#session-parameters-in-connectionstoml) - Advanced session parameter configuration

---

## 💬 Questions?

- **Using schemachange:** Open a [GitHub Discussion](https://github.com/Snowflake-Labs/schemachange/discussions)
- **Found a bug:** Open a [GitHub Issue](https://github.com/Snowflake-Labs/schemachange/issues)
- **Want to contribute:** See [CONTRIBUTING.md](../.github/CONTRIBUTING.md)

---

**Happy deploying! 🚀**
