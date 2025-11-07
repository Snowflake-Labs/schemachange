#!/bin/bash
#
# Example: Key-Pair (JWT) Authentication with Schemachange
#
# This script demonstrates RSA key-pair authentication - RECOMMENDED for CI/CD pipelines.
# Key-pair authentication provides secure, long-lived credentials for automated processes.
#
# Prerequisites:
#   1. Generate an RSA key pair:
#      openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_key.p8 -nocrypt
#   2. Extract the public key:
#      openssl rsa -in snowflake_key.p8 -pubout -out snowflake_key.pub
#   3. Assign the public key to your Snowflake user:
#      ALTER USER <username> SET RSA_PUBLIC_KEY='<public_key_contents>';
#
# Usage:
#   ./keypair_auth_example.sh [demo_project]
#
# Examples:
#   ./keypair_auth_example.sh                    # Uses basics_demo
#   ./keypair_auth_example.sh citibike_demo      # Uses citibike_demo
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default demo project
DEMO_PROJECT="${1:-basics_demo}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Schemachange - Key-Pair (JWT) Authentication Example    ║${NC}"
echo -e "${BLUE}║  (Recommended for CI/CD and Service Accounts)             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "../${DEMO_PROJECT}" ]; then
    echo -e "${RED}Error: Demo project '../${DEMO_PROJECT}' not found${NC}"
    echo -e "${YELLOW}Available projects: basics_demo, citibike_demo, citibike_demo_jinja${NC}"
    exit 1
fi

# Prompt for credentials if not set
if [ -z "$SNOWFLAKE_ACCOUNT" ]; then
    echo -e "${YELLOW}Enter your Snowflake account identifier (e.g., xy12345.us-east-1):${NC}"
    read -r SNOWFLAKE_ACCOUNT
    export SNOWFLAKE_ACCOUNT
fi

if [ -z "$SNOWFLAKE_USER" ]; then
    echo -e "${YELLOW}Enter your Snowflake username:${NC}"
    read -r SNOWFLAKE_USER
    export SNOWFLAKE_USER
fi

# Check for private key file
if [ -z "$SNOWFLAKE_PRIVATE_KEY_PATH" ]; then
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  RSA Key-Pair Setup${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "You need to provide an RSA private key for authentication."
    echo ""
    echo -e "${BLUE}How to generate and configure a key pair:${NC}"
    echo ""
    echo -e "  ${YELLOW}Step 1 - Generate private key (unencrypted):${NC}"
    echo -e "    ${GREEN}openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_key.p8 -nocrypt${NC}"
    echo ""
    echo -e "  ${YELLOW}Step 1 (Alternative) - Generate encrypted private key:${NC}"
    echo -e "    ${GREEN}openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_key.p8${NC}"
    echo -e "    (You'll be prompted for a passphrase)"
    echo ""
    echo -e "  ${YELLOW}Step 2 - Extract public key:${NC}"
    echo -e "    ${GREEN}openssl rsa -in snowflake_key.p8 -pubout -out snowflake_key.pub${NC}"
    echo ""
    echo -e "  ${YELLOW}Step 3 - Assign public key to Snowflake user:${NC}"
    echo -e "    ${GREEN}ALTER USER ${SNOWFLAKE_USER} SET RSA_PUBLIC_KEY='<public_key_contents>';${NC}"
    echo ""
    echo -e "    To get public key contents (without header/footer):"
    echo -e "    ${GREEN}cat snowflake_key.pub | grep -v 'BEGIN PUBLIC KEY' | grep -v 'END PUBLIC KEY' | tr -d '\\n'${NC}"
    echo ""
    echo -e "${YELLOW}Enter the path to your private key file:${NC}"
    echo -e "${YELLOW}(Press Enter to use default: ~/.ssh/snowflake_key.p8)${NC}"
    read -r key_path

    if [ -z "$key_path" ]; then
        SNOWFLAKE_PRIVATE_KEY_PATH="$HOME/.ssh/snowflake_key.p8"
    else
        SNOWFLAKE_PRIVATE_KEY_PATH="$key_path"
    fi

    export SNOWFLAKE_PRIVATE_KEY_PATH
fi

# Verify private key file exists
if [ ! -f "$SNOWFLAKE_PRIVATE_KEY_PATH" ]; then
    echo -e "${RED}Error: Private key file not found: ${SNOWFLAKE_PRIVATE_KEY_PATH}${NC}"
    echo ""
    echo -e "${YELLOW}Please generate a key pair following the instructions above.${NC}"
    exit 1
fi

# Check file permissions
perms=$(stat -f "%A" "$SNOWFLAKE_PRIVATE_KEY_PATH" 2>/dev/null || stat -c "%a" "$SNOWFLAKE_PRIVATE_KEY_PATH" 2>/dev/null)
if [ "$perms" != "600" ] && [ "$perms" != "400" ]; then
    echo -e "${YELLOW}⚠️  Warning: Private key file permissions are not secure (${perms})${NC}"
    echo -e "${YELLOW}   Fixing permissions to 600 (owner read/write only)...${NC}"
    chmod 600 "$SNOWFLAKE_PRIVATE_KEY_PATH"
    echo -e "${GREEN}✓ Permissions updated${NC}"
fi

# Check if key is encrypted (requires passphrase)
if grep -q "ENCRYPTED" "$SNOWFLAKE_PRIVATE_KEY_PATH"; then
    echo ""
    echo -e "${YELLOW}Private key is encrypted. A passphrase is required.${NC}"

    if [ -z "$SNOWFLAKE_PRIVATE_KEY_PASSPHRASE" ]; then
        echo -e "${YELLOW}Enter private key passphrase (input will be hidden):${NC}"
        read -rs SNOWFLAKE_PRIVATE_KEY_PASSPHRASE
        export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE
        echo ""
    fi
fi

# Set authenticator for JWT
export SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"

# Optional parameters
export SNOWFLAKE_ROLE="${SNOWFLAKE_ROLE:-SCHEMACHANGE_DEMO-DEPLOY}"
export SNOWFLAKE_WAREHOUSE="${SNOWFLAKE_WAREHOUSE:-SCHEMACHANGE_DEMO_WH}"
export SNOWFLAKE_DATABASE="${SNOWFLAKE_DATABASE:-SCHEMACHANGE_DEMO}"

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Account:        ${SNOWFLAKE_ACCOUNT}"
echo -e "  User:           ${SNOWFLAKE_USER}"
echo -e "  Authenticator:  ${SNOWFLAKE_AUTHENTICATOR}"
echo -e "  Private Key:    ${SNOWFLAKE_PRIVATE_KEY_PATH}"
if [ -n "$SNOWFLAKE_PRIVATE_KEY_PASSPHRASE" ]; then
    echo -e "  Passphrase:     [SET]"
fi
echo -e "  Role:           ${SNOWFLAKE_ROLE}"
echo -e "  Warehouse:      ${SNOWFLAKE_WAREHOUSE}"
echo -e "  Database:       ${SNOWFLAKE_DATABASE}"
echo -e "  Project:        ${DEMO_PROJECT}"
echo ""

# Test connection with schemachange render
echo -e "${BLUE}Testing connection with 'schemachange render'...${NC}"
echo ""

schemachange render \
  --config-folder ../${DEMO_PROJECT} \
  ../${DEMO_PROJECT}/2_test/V1.0.0__render.sql

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Success! Key-pair authentication is working.${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Run a full deployment:"
    echo -e "     ${GREEN}schemachange deploy --config-folder ../basics_demo${NC}"
    echo ""
    echo -e "  2. Use in CI/CD pipelines:"
    echo -e "     ${GREEN}export SNOWFLAKE_ACCOUNT=\"myaccount.us-east-1\"${NC}"
    echo -e "     ${GREEN}export SNOWFLAKE_USER=\"service_account\"${NC}"
    echo -e "     ${GREEN}export SNOWFLAKE_AUTHENTICATOR=\"snowflake_jwt\"${NC}"
    echo -e "     ${GREEN}export SNOWFLAKE_PRIVATE_KEY_PATH=\"/path/to/key.p8\"${NC}"
    echo -e "     ${GREEN}schemachange deploy --config-folder ./migrations${NC}"
    echo ""
    echo -e "  3. Secure your private key:"
    echo -e "     - Store in CI/CD secrets (as base64 encoded)"
    echo -e "     - Use encrypted keys with passphrase"
    echo -e "     - Set file permissions to 600"
    echo -e "     - Rotate keys periodically"
    echo -e "     - Never commit private keys to version control"
    echo ""
    echo -e "  ${CYAN}Example for CI/CD (GitHub Actions):${NC}"
    echo -e "    ${GREEN}# Store private key as GitHub Secret${NC}"
    echo -e "    ${GREEN}echo \"\${{ secrets.SNOWFLAKE_PRIVATE_KEY }}\" > private_key.p8${NC}"
    echo -e "    ${GREEN}chmod 600 private_key.p8${NC}"
    echo -e "    ${GREEN}export SNOWFLAKE_PRIVATE_KEY_PATH=\"./private_key.p8\"${NC}"
else
    echo ""
    echo -e "${RED}✗ Authentication failed.${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. Verify public key is assigned to user:"
    echo -e "     ${GREEN}DESC USER ${SNOWFLAKE_USER};${NC}"
    echo -e "     (Check RSA_PUBLIC_KEY_FP field)"
    echo ""
    echo -e "  2. Verify private key format:"
    echo -e "     ${GREEN}openssl rsa -in ${SNOWFLAKE_PRIVATE_KEY_PATH} -check${NC}"
    echo ""
    echo -e "  3. Check if key is encrypted (requires passphrase):"
    echo -e "     ${GREEN}grep ENCRYPTED ${SNOWFLAKE_PRIVATE_KEY_PATH}${NC}"
    echo ""
    echo -e "  4. Regenerate key pair if needed (see instructions above)"
    exit 1
fi
