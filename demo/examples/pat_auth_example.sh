#!/bin/bash
#
# Example: Programmatic Access Token (PAT) Authentication with Schemachange
#
# This script demonstrates PAT authentication - RECOMMENDED for CI/CD pipelines.
# PATs provide secure, password-less authentication for automated processes.
#
# Prerequisites:
#   1. Generate a PAT in Snowflake:
#      - Via Snowsight: User Profile > Access Tokens > Generate Token
#      - Via SQL: ALTER USER <username> ADD PROGRAMMATIC ACCESS TOKEN <token_name>;
#   2. Save the token securely (in a file or CI/CD secrets)
#
# IMPORTANT: PATs are passed via SNOWFLAKE_PASSWORD (NOT SNOWFLAKE_TOKEN_FILE_PATH)
#            The Snowflake connector automatically detects PATs from regular passwords.
#            Do NOT set SNOWFLAKE_AUTHENTICATOR - it defaults to "snowflake" which is correct for PATs.
#
# Usage:
#   ./pat_auth_example.sh [demo_project]
#
# Examples:
#   ./pat_auth_example.sh                    # Uses basics_demo
#   ./pat_auth_example.sh citibike_demo      # Uses citibike_demo
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
echo -e "${BLUE}║  Schemachange - PAT Authentication Example               ║${NC}"
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

# Check if PAT is already set
if [ -z "$SNOWFLAKE_PASSWORD" ]; then
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Programmatic Access Token (PAT) Setup${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "You need to provide a Programmatic Access Token (PAT)."
    echo ""
    echo -e "${BLUE}How to generate a PAT:${NC}"
    echo ""
    echo -e "  ${YELLOW}Option 1 - Via Snowsight:${NC}"
    echo -e "    1. Log in to Snowsight"
    echo -e "    2. Go to your User Profile"
    echo -e "    3. Navigate to 'Access Tokens'"
    echo -e "    4. Click 'Generate Token'"
    echo -e "    5. Copy and save the token securely"
    echo ""
    echo -e "  ${YELLOW}Option 2 - Via SQL:${NC}"
    echo -e "    ${GREEN}ALTER USER ${SNOWFLAKE_USER} ADD PROGRAMMATIC ACCESS TOKEN my_token;${NC}"
    echo ""
    echo -e "${BLUE}How to provide the PAT:${NC}"
    echo -e "  ${YELLOW}A)${NC} Enter it directly (for testing)"
    echo -e "  ${YELLOW}B)${NC} Read from a file (recommended for local development)"
    echo ""
    echo -e "${YELLOW}Choose option (A/B):${NC}"
    read -r pat_option

    if [ "$pat_option" = "A" ] || [ "$pat_option" = "a" ]; then
        # Direct entry
        echo -e "${YELLOW}Paste your PAT token (input will be hidden):${NC}"
        read -rs SNOWFLAKE_PASSWORD
        export SNOWFLAKE_PASSWORD
        echo ""

    elif [ "$pat_option" = "B" ] || [ "$pat_option" = "b" ]; then
        # From file
        echo -e "${YELLOW}Enter the path to your PAT token file:${NC}"
        echo -e "${YELLOW}(Press Enter to use default: ~/.snowflake/pat_token.txt)${NC}"
        read -r token_file_path

        if [ -z "$token_file_path" ]; then
            token_file_path="$HOME/.snowflake/pat_token.txt"
        fi

        # Check if file exists
        if [ ! -f "$token_file_path" ]; then
            echo ""
            echo -e "${RED}Token file not found: ${token_file_path}${NC}"
            echo ""
            echo -e "${YELLOW}Would you like to create it now? (y/n)${NC}"
            read -r create_file

            if [ "$create_file" = "y" ] || [ "$create_file" = "Y" ]; then
                # Create directory if it doesn't exist
                mkdir -p "$(dirname "$token_file_path")"

                echo -e "${YELLOW}Paste your PAT token (input will be hidden):${NC}"
                read -rs pat_token
                echo ""

                # Save token to file with secure permissions
                echo "$pat_token" > "$token_file_path"
                chmod 600 "$token_file_path"

                echo -e "${GREEN}✓ Token saved to: ${token_file_path}${NC}"
                echo -e "${GREEN}✓ File permissions set to 600 (owner read/write only)${NC}"
            else
                echo -e "${RED}Cannot proceed without a PAT. Exiting.${NC}"
                exit 1
            fi
        fi

        # Verify token file exists and has correct permissions
        if [ ! -f "$token_file_path" ]; then
            echo -e "${RED}Error: Token file not found: ${token_file_path}${NC}"
            exit 1
        fi

        # Check file permissions
        perms=$(stat -f "%A" "$token_file_path" 2>/dev/null || stat -c "%a" "$token_file_path" 2>/dev/null)
        if [ "$perms" != "600" ]; then
            echo -e "${YELLOW}⚠️  Warning: Token file permissions are not secure (${perms})${NC}"
            echo -e "${YELLOW}   Fixing permissions to 600 (owner read/write only)...${NC}"
            chmod 600 "$token_file_path"
            echo -e "${GREEN}✓ Permissions updated${NC}"
        fi

        # Read PAT from file
        export SNOWFLAKE_PASSWORD=$(cat "$token_file_path")
        echo -e "${GREEN}✓ PAT loaded from file${NC}"
    else
        echo -e "${RED}Invalid option. Exiting.${NC}"
        exit 1
    fi
fi

# Optional parameters
export SNOWFLAKE_ROLE="${SNOWFLAKE_ROLE:-SCHEMACHANGE_DEMO-DEPLOY}"
export SNOWFLAKE_WAREHOUSE="${SNOWFLAKE_WAREHOUSE:-SCHEMACHANGE_DEMO_WH}"
export SNOWFLAKE_DATABASE="${SNOWFLAKE_DATABASE:-SCHEMACHANGE_DEMO}"

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Account:    ${SNOWFLAKE_ACCOUNT}"
echo -e "  User:       ${SNOWFLAKE_USER}"
echo -e "  Password:   [PAT SET]"
echo -e "  Role:       ${SNOWFLAKE_ROLE}"
echo -e "  Warehouse:  ${SNOWFLAKE_WAREHOUSE}"
echo -e "  Database:   ${SNOWFLAKE_DATABASE}"
echo -e "  Project:    ${DEMO_PROJECT}"
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Important: How PAT Authentication Works${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "PATs are passed via ${GREEN}SNOWFLAKE_PASSWORD${NC} (NOT SNOWFLAKE_TOKEN_FILE_PATH)"
echo -e "The Snowflake connector automatically detects PATs from regular passwords."
echo -e "Authenticator defaults to 'snowflake' - no need to set it explicitly."
echo ""

# Test connection with schemachange render
echo -e "${BLUE}Testing connection with 'schemachange render'...${NC}"
echo ""

schemachange render \
  --config-folder ../${DEMO_PROJECT} \
  ../${DEMO_PROJECT}/2_test/V1.0.0__render.sql

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Success! PAT authentication is working.${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Run a full deployment:"
    echo -e "     ${GREEN}schemachange deploy --config-folder ../basics_demo${NC}"
    echo ""
    echo -e "  2. Use in CI/CD pipelines:"
    echo -e "     ${GREEN}# Store PAT in CI/CD secrets${NC}"
    echo -e "     ${GREEN}export SNOWFLAKE_ACCOUNT=\"myaccount.us-east-1\"${NC}"
    echo -e "     ${GREEN}export SNOWFLAKE_USER=\"service_account\"${NC}"
    echo -e "     ${GREEN}export SNOWFLAKE_PASSWORD=\"\${{ secrets.SNOWFLAKE_PAT }}\"${NC}"
    echo -e "     ${GREEN}schemachange deploy --config-folder ./migrations${NC}"
    echo ""
    echo -e "  3. Use with token file:"
    echo -e "     ${GREEN}export SNOWFLAKE_PASSWORD=\$(cat ~/.snowflake/pat_token.txt)${NC}"
    echo -e "     ${GREEN}schemachange deploy --config-folder ./migrations${NC}"
    echo ""
    echo -e "  ${CYAN}Important Security Notes:${NC}"
    echo -e "     - PATs use SNOWFLAKE_PASSWORD, not SNOWFLAKE_TOKEN_FILE_PATH"
    echo -e "     - PATs are NOT OAuth (don't set SNOWFLAKE_AUTHENTICATOR=oauth)"
    echo -e "     - Store PATs in CI/CD secrets or secure vaults"
    echo -e "     - Set file permissions to 600 if storing in files"
    echo -e "     - Rotate PATs regularly"
    echo -e "     - Never commit PATs to version control"
else
    echo ""
    echo -e "${RED}✗ Authentication failed.${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. Verify PAT is valid: Check Snowsight > User Profile > Access Tokens"
    echo -e "  2. Check PAT value: ${GREEN}echo \$SNOWFLAKE_PASSWORD${NC}"
    echo -e "  3. Verify user has necessary privileges"
    echo -e "  4. Check account identifier is correct"
    echo -e "  5. Ensure you're using SNOWFLAKE_PASSWORD (not SNOWFLAKE_TOKEN_FILE_PATH)"
    echo ""
    echo -e "  ${CYAN}Common mistakes:${NC}"
    echo -e "     ✗ Setting SNOWFLAKE_AUTHENTICATOR=oauth (don't do this for PATs)"
    echo -e "     ✗ Using SNOWFLAKE_TOKEN_FILE_PATH (use SNOWFLAKE_PASSWORD instead)"
    echo -e "     ✓ Just set SNOWFLAKE_PASSWORD with your PAT value"
    exit 1
fi
