# Quick Start Guide - Authentication Examples

Get started with schemachange authentication in 3 simple steps!

## Step 1: Choose Your Authentication Method

| Method | Best For | Setup Time | Script |
|--------|----------|------------|--------|
| **PAT (Programmatic Access Token)** | CI/CD, Service Accounts | 5 min | `./pat_auth_example.sh` |
| **Key-Pair (JWT)** | CI/CD, Long-term automation | 10 min | `./keypair_auth_example.sh` |
| **SSO (External Browser)** | Human users, Interactive | 2 min | `./sso_auth_example.sh` |
| **Password** | Legacy/Development | 2 min | `./password_auth_example.sh` |

💡 **Recommendation:** Use PAT or Key-Pair for production/CI-CD. Password auth requires MFA by Nov 2025.

## Step 2: Run the Example Script

```bash
cd demo/examples

# Example: Test PAT authentication
./pat_auth_example.sh
```

The script will:
1. ✓ Prompt for your Snowflake credentials
2. ✓ Guide you through setup (create token file, etc.)
3. ✓ Test the connection
4. ✓ Show you how to use it in real deployments

## Step 3: Deploy to Demo Projects

Once authentication is working, try a real deployment:

```bash
# Deploy to basics_demo
schemachange deploy --config-folder ../basics_demo

# Or specify a different demo
./pat_auth_example.sh citibike_demo
```

## What Each Script Does

### PAT Authentication (`./pat_auth_example.sh`)
- Prompts for PAT value or reads from file
- Sets PAT via SNOWFLAKE_PASSWORD environment variable
- Tests connection with your PAT
- Shows CI/CD integration examples

**When to use:** Service accounts, GitHub Actions, GitLab CI, automated pipelines

**Important:** PATs use SNOWFLAKE_PASSWORD (not SNOWFLAKE_TOKEN_FILE_PATH) and the default `snowflake` authenticator

### Key-Pair Authentication (`./keypair_auth_example.sh`)
- Guides you through RSA key generation
- Helps configure the public key in Snowflake
- Handles encrypted keys with passphrases
- Tests JWT authentication

**When to use:** Long-lived service accounts, infrastructure-as-code, Terraform

### SSO Authentication (`./sso_auth_example.sh`)
- Opens browser for SSO login
- Supports MFA automatically
- Caches token to minimize prompts
- Works with any SAML provider

**When to use:** Human users, development environments, interactive sessions

### Password Authentication (`./password_auth_example.sh`)
- Simple username/password
- Shows MFA deprecation warning
- Not recommended for production

**When to use:** Quick testing only (deprecated for production)

## Troubleshooting

**"PAT authentication failed"**
```bash
# Verify PAT is set correctly
echo $SNOWFLAKE_PASSWORD  # Should show your PAT value

# If using a file:
echo "your_pat_here" > ~/.snowflake/pat_token.txt
chmod 600 ~/.snowflake/pat_token.txt
export SNOWFLAKE_PASSWORD=$(cat ~/.snowflake/pat_token.txt)

# Common mistake: Don't set SNOWFLAKE_AUTHENTICATOR=oauth for PATs!
```

**"Private key authentication failed"**
```bash
# Verify key is in PEM format
openssl rsa -in snowflake_key.p8 -check

# Verify public key is assigned in Snowflake
DESC USER your_username;
```

**"Browser doesn't open" (SSO)**
```bash
# For headless systems, use PAT or key-pair instead
./pat_auth_example.sh
```

## Next Steps

After successful authentication:

1. **Review the demos:**
   - `basics_demo/` - Simple example with schema creation
   - `citibike_demo/` - Real-world data loading
   - `citibike_demo_jinja/` - Advanced Jinja templating

2. **Read the docs:**
   - [Main README](../../README.md) - Complete documentation
   - [Demo README](../README.MD) - Demo-specific info
   - [Examples README](README.md) - Detailed auth guide

3. **Set up for your project:**
   - Copy environment variable exports to your CI/CD
   - Add credentials to your secrets manager
   - Test with a small migration first

## Security Reminders

✓ Never commit credentials to version control
✓ Use secure file permissions (600) for tokens/keys
✓ Rotate credentials regularly
✓ Use PAT or key-pair for automation
✓ Enable MFA for human users
✓ Store secrets in CI/CD secrets or vault

## Need Help?

- Check [README.md](README.md) for detailed documentation
- Open an issue on GitHub
- Review Snowflake connector documentation
