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
export SNOWFLAKE_ACCOUNT="myaccount.us-east-1"
export SNOWFLAKE_USER="service_account"
export SNOWFLAKE_PASSWORD="<your_pat_token>"  # Use a PAT for MFA accounts
export SNOWFLAKE_ROLE="SCHEMACHANGE_DEMO-DEPLOY"
export SNOWFLAKE_WAREHOUSE="SCHEMACHANGE_DEMO_WH"
export SNOWFLAKE_DATABASE="SCHEMACHANGE_DEMO"

schemachange deploy --config-folder ./demo/basics_demo
```

**📚 Need JWT, SSO, or other authentication methods?** See the [Authentication Guide](../README.md#authentication) in the main README.

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
