# Schemachange Authentication Examples

This directory contains practical examples for testing different Snowflake authentication methods with schemachange.

## Quick Start

1. **Choose your authentication method** from the examples below
2. **Follow the setup instructions** for that method
3. **Run the example script** to test your configuration
4. **Verify the connection** works before using in production

## Authentication Methods

### 1. Password Authentication (Basic)
**File:** `password_auth_example.sh`

Simple username/password authentication. **Note:** Snowflake is enforcing MFA for all password authentication by November 2025.

```bash
./examples/password_auth_example.sh
```

### 2. Programmatic Access Token (PAT) - RECOMMENDED for CI/CD
**File:** `pat_auth_example.sh`

Secure, password-less authentication using Snowflake Programmatic Access Tokens. Best for:
- CI/CD pipelines
- Service accounts
- Automated processes

```bash
./examples/pat_auth_example.sh
```

### 3. Key-Pair (JWT) Authentication - RECOMMENDED for CI/CD
**File:** `keypair_auth_example.sh`

RSA key-pair authentication. Best for:
- CI/CD pipelines
- Service accounts
- Automated processes with long-lived credentials

```bash
./examples/keypair_auth_example.sh
```

### 4. External Browser (SSO) Authentication
**File:** `sso_auth_example.sh`

Browser-based SSO authentication. Best for:
- Human users with SSO
- Interactive sessions
- MFA-enabled accounts

```bash
./examples/sso_auth_example.sh
```

## Credential Templates

Template files are provided in the `templates/` directory. Copy and populate them with your credentials:

```bash
# Copy templates
cp templates/token.txt.template ~/.snowflake/token.txt
cp templates/connections.toml.template ~/.snowflake/connections.toml

# Edit with your credentials
nano ~/.snowflake/token.txt
```

**Security Note:** Never commit actual credentials to version control!

## Testing Against Demo Projects

All example scripts support testing against the included demo projects:

```bash
# Test with basics_demo
./examples/pat_auth_example.sh basics_demo

# Test with citibike_demo
./examples/keypair_auth_example.sh citibike_demo

# Test with citibike_demo_jinja
./examples/sso_auth_example.sh citibike_demo_jinja
```

## Environment Variables Reference

All authentication methods support the following base configuration:

| Variable | Description | Required |
|----------|-------------|----------|
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier | Yes |
| `SNOWFLAKE_USER` | Username | Yes |
| `SNOWFLAKE_ROLE` | Role to use | No |
| `SNOWFLAKE_WAREHOUSE` | Warehouse to use | No |
| `SNOWFLAKE_DATABASE` | Database to use | No |
| `SNOWFLAKE_SCHEMA` | Schema to use | No |

### Method-Specific Variables

**Password Authentication:**
- `SNOWFLAKE_PASSWORD` - User password

**PAT Authentication:**
- `SNOWFLAKE_PASSWORD` - Programmatic Access Token value
- Note: Authenticator defaults to `snowflake` (no need to set)
- The connector automatically detects PATs from regular passwords

**OAuth Authentication (External OAuth Providers):**
- `SNOWFLAKE_AUTHENTICATOR=oauth`
- `SNOWFLAKE_TOKEN_FILE_PATH` - Path to OAuth token file

**Key-Pair Authentication:**
- `SNOWFLAKE_AUTHENTICATOR=snowflake_jwt`
- `SNOWFLAKE_PRIVATE_KEY_PATH` - Path to private key file
- `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` - Passphrase (if key is encrypted)

**SSO Authentication:**
- `SNOWFLAKE_AUTHENTICATOR=externalbrowser`

## Troubleshooting

### Common Issues

**PAT Authentication:**
```bash
# Error: Authentication failed with PAT
# Solution: Verify PAT is valid and passed correctly
echo $SNOWFLAKE_PASSWORD  # Should show your PAT value

# If using a file:
cat ~/.snowflake/pat_token.txt  # Verify token is readable
chmod 600 ~/.snowflake/pat_token.txt  # Ensure secure permissions
export SNOWFLAKE_PASSWORD=$(cat ~/.snowflake/pat_token.txt)
```

**Key-Pair Authentication:**
```bash
# Error: Invalid private key format
# Solution: Ensure key is in PEM format
openssl rsa -in snowflake_key.p8 -check
```

**SSO Authentication:**
```bash
# Error: Browser doesn't open
# Solution: Ensure you're on a system with a browser
# For headless systems, use PAT or key-pair instead
```

### Getting Help

1. Check the main [README.md](../../README.md) for detailed documentation
2. Review [demo/README.MD](../README.MD) for environment variable details
3. Open an issue on GitHub if you encounter problems

## Security Best Practices

1. **Never hardcode credentials** in scripts
2. **Use environment variables** or secure vaults
3. **Set restrictive permissions** on credential files (600)
4. **Rotate credentials** regularly
5. **Use PAT or key-pair** for automated processes
6. **Enable MFA** for human users
7. **Review access logs** periodically

## Next Steps

After testing authentication:
1. Review the [basics_demo](../basics_demo/) for a simple example
2. Try the [citibike_demo](../citibike_demo/) for a more complex scenario
3. Explore [citibike_demo_jinja](../citibike_demo_jinja/) for Jinja templating
4. Read the main [README.md](../../README.md) for full documentation
