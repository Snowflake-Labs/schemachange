# Schemachange Authentication Examples

This directory provides command-line examples for authenticating to Snowflake with schemachange using different authentication methods.

## Quick Reference

Choose your authentication method and set the appropriate environment variables:

### 1. Password Authentication (Basic)

```bash
export SNOWFLAKE_ACCOUNT="myaccount"
export SNOWFLAKE_USER="myuser"
export SNOWFLAKE_PASSWORD="mypassword"
export SNOWFLAKE_ROLE="MY_ROLE"
export SNOWFLAKE_WAREHOUSE="MY_WH"
schemachange deploy --config-folder ./demo/basics_demo
```

**Note:** Snowflake enforces MFA for password authentication (November 2025+).

### 2. Programmatic Access Token (PAT) - RECOMMENDED for CI/CD

```bash
export SNOWFLAKE_ACCOUNT="myaccount"
export SNOWFLAKE_USER="service_account"
export SNOWFLAKE_PASSWORD="<your_pat_token>"
export SNOWFLAKE_ROLE="MY_ROLE"
export SNOWFLAKE_WAREHOUSE="MY_WH"
schemachange deploy --config-folder ./demo/basics_demo
```

**Secure option** (read from file):
```bash
export SNOWFLAKE_PASSWORD=$(cat ~/.snowflake/pat_token.txt)
```

### 3. Key-Pair (JWT) Authentication - RECOMMENDED for CI/CD

```bash
export SNOWFLAKE_ACCOUNT="myaccount"
export SNOWFLAKE_USER="myuser"
export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
export SNOWFLAKE_PRIVATE_KEY_PATH="~/.ssh/snowflake_key.p8"
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE="key_password"
export SNOWFLAKE_ROLE="MY_ROLE"
export SNOWFLAKE_WAREHOUSE="MY_WH"
schemachange deploy --config-folder ./demo/basics_demo
```

### 4. External Browser (SSO) Authentication

```bash
export SNOWFLAKE_ACCOUNT="myaccount"
export SNOWFLAKE_USER="myuser"
export SNOWFLAKE_AUTHENTICATOR="externalbrowser"
export SNOWFLAKE_ROLE="MY_ROLE"
export SNOWFLAKE_WAREHOUSE="MY_WH"
schemachange deploy --config-folder ./demo/basics_demo
```

## Environment Variables Reference

### Base Configuration (All Methods)

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
- Authenticator defaults to `snowflake` (no need to set)

**Key-Pair Authentication:**
- `SNOWFLAKE_AUTHENTICATOR=snowflake_jwt`
- `SNOWFLAKE_PRIVATE_KEY_PATH` - Path to private key file
- `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` - Passphrase (if encrypted)

**SSO Authentication:**
- `SNOWFLAKE_AUTHENTICATOR=externalbrowser`

## Troubleshooting

### PAT Authentication

```bash
# Verify PAT is set correctly
echo $SNOWFLAKE_PASSWORD

# If using a file, ensure it's readable
cat ~/.snowflake/pat_token.txt
chmod 600 ~/.snowflake/pat_token.txt
```

### Key-Pair Authentication

```bash
# Verify private key format
openssl rsa -in ~/.ssh/snowflake_key.p8 -check

# Generate a new key pair if needed
openssl genrsa -out snowflake_key.p8 2048
openssl rsa -in snowflake_key.p8 -pubout -out snowflake_key.pub
```

### SSO Authentication

Ensure you're on a system with a browser. For headless systems, use PAT or key-pair authentication instead.

## Security Best Practices

1. **Never hardcode credentials** in scripts or version control
2. **Use environment variables** or secure secret managers
3. **Set restrictive permissions** on credential files (chmod 600)
4. **Rotate credentials** regularly
5. **Use PAT or key-pair** for automated processes
6. **Enable MFA** for human users

## Next Steps

After setting up authentication:
1. Test with [basics_demo](../basics_demo/)
2. Try [citibike_demo](../citibike_demo/)
3. Explore [citibike_demo_jinja](../citibike_demo_jinja/)
4. Read the main [README.md](../../README.md) for full documentation
