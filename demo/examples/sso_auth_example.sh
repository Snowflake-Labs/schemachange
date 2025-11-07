#!/bin/bash
#
# Example: External Browser (SSO) Authentication with Schemachange
#
# This script demonstrates browser-based SSO authentication.
# Best for human users with SSO/SAML and MFA-enabled accounts.
#
# Prerequisites:
#   - SSO/SAML configured in your Snowflake account
#   - A web browser available on the system
#   - For headless systems, use PAT or key-pair authentication instead
#
# Usage:
#   ./sso_auth_example.sh [demo_project]
#
# Examples:
#   ./sso_auth_example.sh                    # Uses basics_demo
#   ./sso_auth_example.sh citibike_demo      # Uses citibike_demo
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
echo -e "${BLUE}║  Schemachange - SSO Authentication Example               ║${NC}"
echo -e "${BLUE}║  (Browser-based SSO/SAML with MFA support)                ║${NC}"
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

# Set authenticator for external browser (SSO)
export SNOWFLAKE_AUTHENTICATOR="externalbrowser"

# Optional parameters
export SNOWFLAKE_ROLE="${SNOWFLAKE_ROLE:-SCHEMACHANGE_DEMO-DEPLOY}"
export SNOWFLAKE_WAREHOUSE="${SNOWFLAKE_WAREHOUSE:-SCHEMACHANGE_DEMO_WH}"
export SNOWFLAKE_DATABASE="${SNOWFLAKE_DATABASE:-SCHEMACHANGE_DEMO}"

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Account:        ${SNOWFLAKE_ACCOUNT}"
echo -e "  User:           ${SNOWFLAKE_USER}"
echo -e "  Authenticator:  ${SNOWFLAKE_AUTHENTICATOR}"
echo -e "  Role:           ${SNOWFLAKE_ROLE}"
echo -e "  Warehouse:      ${SNOWFLAKE_WAREHOUSE}"
echo -e "  Database:       ${SNOWFLAKE_DATABASE}"
echo -e "  Project:        ${DEMO_PROJECT}"
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Browser Authentication${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}A browser window will open for authentication.${NC}"
echo ""
echo -e "Steps:"
echo -e "  1. Your default browser will open automatically"
echo -e "  2. Log in with your SSO credentials"
echo -e "  3. Complete MFA if prompted"
echo -e "  4. Return to this terminal once authenticated"
echo ""
echo -e "${BLUE}Note:${NC} The authentication token will be cached to minimize"
echo -e "      future browser prompts (see Snowflake docs for cache details)."
echo ""
echo -e "${YELLOW}Press Enter to continue...${NC}"
read -r

# Test connection with schemachange render
echo -e "${BLUE}Testing connection with 'schemachange render'...${NC}"
echo -e "${YELLOW}(Browser will open shortly)${NC}"
echo ""

schemachange render \
  --config-folder ../${DEMO_PROJECT} \
  ../${DEMO_PROJECT}/2_test/V1.0.0__render.sql

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Success! SSO authentication is working.${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Run a full deployment:"
    echo -e "     ${GREEN}schemachange deploy --config-folder ../basics_demo${NC}"
    echo ""
    echo -e "  2. Use in interactive sessions:"
    echo -e "     ${GREEN}export SNOWFLAKE_ACCOUNT=\"myaccount.us-east-1\"${NC}"
    echo -e "     ${GREEN}export SNOWFLAKE_USER=\"user@company.com\"${NC}"
    echo -e "     ${GREEN}export SNOWFLAKE_AUTHENTICATOR=\"externalbrowser\"${NC}"
    echo -e "     ${GREEN}schemachange deploy --config-folder ./migrations${NC}"
    echo ""
    echo -e "  3. Token caching:"
    echo -e "     - Snowflake caches SSO tokens to reduce browser prompts"
    echo -e "     - Cache location: ~/.snowflake/ directory"
    echo -e "     - Configure cache behavior: See Snowflake connector docs"
    echo ""
    echo -e "  ${CYAN}For automated/headless systems:${NC}"
    echo -e "    SSO requires a browser. Use these alternatives instead:"
    echo -e "    - PAT:      ${GREEN}./pat_auth_example.sh${NC}"
    echo -e "    - Key-Pair: ${GREEN}./keypair_auth_example.sh${NC}"
else
    echo ""
    echo -e "${RED}✗ Authentication failed.${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. Verify SSO is configured in your Snowflake account"
    echo -e "  2. Check that your browser opened and you completed login"
    echo -e "  3. Ensure you have network access to Snowflake"
    echo -e "  4. Try clearing Snowflake token cache:"
    echo -e "     ${GREEN}rm -rf ~/.snowflake/token_cache/*${NC}"
    echo ""
    echo -e "  ${CYAN}For headless/CI-CD systems:${NC}"
    echo -e "     SSO requires a browser. Use PAT or key-pair authentication:"
    echo -e "     - ${GREEN}./pat_auth_example.sh${NC}"
    echo -e "     - ${GREEN}./keypair_auth_example.sh${NC}"
    exit 1
fi
