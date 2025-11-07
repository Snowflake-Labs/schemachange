# Quick Start Guide - Authentication Examples

Get started with schemachange authentication in minutes!

## Step 1: Choose Your Authentication Method

| Method | Best For | Setup Time |
|--------|----------|------------|
| **PAT (Programmatic Access Token)** | CI/CD, Service Accounts | 5 min |
| **Key-Pair (JWT)** | CI/CD, Long-term automation | 10 min |
| **SSO (External Browser)** | Human users, Interactive | 2 min |
| **Password** | Development only | 2 min |

💡 **Recommendation:** Use PAT or Key-Pair for production/CI-CD. Password auth requires MFA (Nov 2025+).

## Step 2: Set Environment Variables

### PAT Authentication (Recommended for CI/CD)

```bash
export SNOWFLAKE_ACCOUNT="myaccount"
export SNOWFLAKE_USER="service_account"
export SNOWFLAKE_PASSWORD="<your_pat_token>"
export SNOWFLAKE_ROLE="MY_ROLE"
export SNOWFLAKE_WAREHOUSE="MY_WH"
```

### Key-Pair Authentication

```bash
export SNOWFLAKE_ACCOUNT="myaccount"
export SNOWFLAKE_USER="myuser"
export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
export SNOWFLAKE_PRIVATE_KEY_PATH="~/.ssh/snowflake_key.p8"
export SNOWFLAKE_ROLE="MY_ROLE"
export SNOWFLAKE_WAREHOUSE="MY_WH"
```

### SSO Authentication

```bash
export SNOWFLAKE_ACCOUNT="myaccount"
export SNOWFLAKE_USER="myuser"
export SNOWFLAKE_AUTHENTICATOR="externalbrowser"
export SNOWFLAKE_ROLE="MY_ROLE"
export SNOWFLAKE_WAREHOUSE="MY_WH"
```

### Password Authentication

```bash
export SNOWFLAKE_ACCOUNT="myaccount"
export SNOWFLAKE_USER="myuser"
export SNOWFLAKE_PASSWORD="mypassword"
export SNOWFLAKE_ROLE="MY_ROLE"
export SNOWFLAKE_WAREHOUSE="MY_WH"
```

## Step 3: Test Your Configuration

```bash
# Test with basics_demo
cd demo
schemachange deploy --config-folder ./basics_demo

# Or try other demos
schemachange deploy --config-folder ./citibike_demo
```

## Troubleshooting

### PAT Authentication Failed

```bash
# Verify PAT is set
echo $SNOWFLAKE_PASSWORD

# If using a file
export SNOWFLAKE_PASSWORD=$(cat ~/.snowflake/pat_token.txt)
chmod 600 ~/.snowflake/pat_token.txt

# Common mistake: Don't set SNOWFLAKE_AUTHENTICATOR for PATs!
```

### Key-Pair Authentication Failed

```bash
# Verify key format
openssl rsa -in ~/.ssh/snowflake_key.p8 -check

# Verify public key is assigned in Snowflake
DESC USER your_username;
```

### SSO Browser Doesn't Open

For headless systems, use PAT or key-pair authentication instead.

## Next Steps

1. **Review the demos:**
   - `basics_demo/` - Simple schema creation
   - `citibike_demo/` - Real-world data loading
   - `citibike_demo_jinja/` - Jinja templating

2. **Read the docs:**
   - [Main README](../../README.md) - Complete documentation
   - [Examples README](README.md) - Detailed authentication guide

3. **Set up for production:**
   - Add credentials to CI/CD secrets
   - Test with small migrations first
   - Enable appropriate logging

## Security Reminders

✓ Never commit credentials to version control
✓ Use secure file permissions (600) for tokens/keys
✓ Rotate credentials regularly
✓ Use PAT or key-pair for automation
✓ Store secrets in CI/CD secrets manager

## Need Help?

- Check [README.md](README.md) for detailed documentation
- Open an issue on GitHub
- Review Snowflake connector documentation
