#!/bin/bash
# Quick test runner for deploy.py changes
# Usage: ./test_deploy.sh [options]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing deploy.py changes...${NC}"
echo ""

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
else
    source .venv/bin/activate
fi

# Parse arguments
case "${1:-all}" in
    "deploy")
        echo -e "${BLUE}Running deploy tests only...${NC}"
        python -m pytest tests/test_deploy.py -v
        ;;
    "all")
        echo -e "${BLUE}Running all tests...${NC}"
        python -m pytest tests/ -v
        ;;
    "quick")
        echo -e "${BLUE}Running deploy tests (quick)...${NC}"
        python -m pytest tests/test_deploy.py -v --tb=line
        ;;
    "coverage")
        echo -e "${BLUE}Running deploy tests with coverage...${NC}"
        python -m pytest tests/test_deploy.py --cov=schemachange.deploy --cov-report=term-missing --cov-report=html
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "lint")
        echo -e "${BLUE}Running linter on deploy files...${NC}"
        ruff check schemachange/deploy.py tests/test_deploy.py
        ;;
    *)
        echo "Usage: $0 [deploy|all|quick|coverage|lint]"
        echo ""
        echo "  deploy   - Run only deploy tests (verbose)"
        echo "  all      - Run all tests (verbose)"
        echo "  quick    - Run deploy tests with minimal output"
        echo "  coverage - Run deploy tests with coverage report"
        echo "  lint     - Run linter on deploy files"
        echo ""
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✓ Tests completed successfully!${NC}"
