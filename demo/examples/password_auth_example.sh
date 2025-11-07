#!/bin/bash
#
# Example: Password Authentication with Schemachange
#
# This script demonstrates basic password authentication.
# WARNING: Snowflake is enforcing MFA for password authentication by November 2025.
# For production use, consider PAT or key-pair authentication instead.
#
# Usage:
#   ./password_auth_example.sh [demo_project]
#
# Examples:
#   ./password_auth_example.sh                    # Uses basics_demo
#   ./password_auth_example.sh citibike_demo      # Uses citibike_demo
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default demo project
DEMO_PROJECT="${1:-basics_demo}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Schemachange - Password Authentication Example          ║${NC}"
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

if [ -z "$SNOWFLAKE_PASSWORD" ]; then
    echo -e "${YELLOW}Enter your Snowflake password:${NC}"
    read -rs SNOWFLAKE_PASSWORD
    export SNOWFLAKE_PASSWORD
    echo ""
fi

# Optional parameters
export SNOWFLAKE_ROLE="${SNOWFLAKE_ROLE:-SCHEMACHANGE_DEMO-DEPLOY}"
export SNOWFLAKE_WAREHOUSE="${SNOWFLAKE_WAREHOUSE:-SCHEMACHANGE_DEMO_WH}"
export SNOWFLAKE_DATABASE="${SNOWFLAKE_DATABASE:-SCHEMACHANGE_DEMO}"

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Account:   ${SNOWFLAKE_ACCOUNT}"
echo -e "  User:      ${SNOWFLAKE_USER}"
echo -e "  Role:      ${SNOWFLAKE_ROLE}"
echo -e "  Warehouse: ${SNOWFLAKE_WAREHOUSE}"
echo -e "  Database:  ${SNOWFLAKE_DATABASE}"
echo -e "  Project:   ${DEMO_PROJECT}"
echo ""

# Security warning
echo -e "${YELLOW}⚠️  Security Notice:${NC}"
echo -e "${YELLOW}   Snowflake is enforcing MFA for password authentication by November 2025.${NC}"
echo -e "${YELLOW}   For production/CI-CD use, consider PAT or key-pair authentication.${NC}"
echo ""

# Test connection with schemachange render
echo -e "${BLUE}Testing connection with 'schemachange render'...${NC}"
echo ""

schemachange render \
  --config-folder ../${DEMO_PROJECT} \
  ../${DEMO_PROJECT}/2_test/V1.0.0__render.sql

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Success! Password authentication is working.${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Run a full deployment:"
    echo -e "     ${GREEN}schemachange deploy --config-folder ../basics_demo${NC}"
    echo ""
    echo -e "  2. Try other authentication methods:"
    echo -e "     - PAT:      ${GREEN}./pat_auth_example.sh${NC}"
    echo -e "     - Key-Pair: ${GREEN}./keypair_auth_example.sh${NC}"
    echo -e "     - SSO:      ${GREEN}./sso_auth_example.sh${NC}"
else
    echo ""
    echo -e "${RED}✗ Authentication failed. Please check your credentials.${NC}"
    exit 1
fi
