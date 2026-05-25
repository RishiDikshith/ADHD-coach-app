#!/bin/bash
# ==============================================================================
# ADHD Productivity MVP - Backend Test and Quality Runner
# ==============================================================================
# This script runs all code quality linters, formatters, and automated tests.
# Exit immediately if a command exits with a non-zero status.
set -e

# Define console text colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

echo -e "${YELLOW}=====================================================${NC}"
echo -e "${YELLOW}Starting ADHD Productivity Backend Quality Pipeline...${NC}"
echo -e "${YELLOW}=====================================================${NC}"

# Check Python environment
python3 -c "import sys; print(f'Using Python {sys.version}')"

# Run isort check
echo -e "\n${YELLOW}[1/4] Checking imports formatting with isort...${NC}"
python3 -m isort --check-only src/
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Import sorting check passed!${NC}"
else
    echo -e "${RED}✗ Import sorting check failed! Run 'isort src/' to fix.${NC}"
    exit 1
fi

# Run black check
echo -e "\n${YELLOW}[2/4] Checking code formatting with black...${NC}"
python3 -m black --check src/
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Code formatting check passed!${NC}"
else
    echo -e "${RED}✗ Code formatting check failed! Run 'black src/' to fix.${NC}"
    exit 1
fi

# Run flake8 linter
echo -e "\n${YELLOW}[3/4] Linting code with flake8...${NC}"
python3 -m flake8 src/
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Linter checks passed!${NC}"
else
    echo -e "${RED}✗ Linter checks failed! Review the errors above.${NC}"
    exit 1
fi

# Run pytest suite with coverage
echo -e "\n${YELLOW}[4/4] Running automated tests with pytest...${NC}"
export DATABASE_URL="sqlite:///:memory:"
export GROQ_API_KEY="mock_groq_key_for_ci"
python3 -m pytest

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}=====================================================${NC}"
    echo -e "${GREEN}★ SUCCESS: All backend checks and tests passed! ★${NC}"
    echo -e "${GREEN}=====================================================${NC}"
else
    echo -e "\n${RED}=====================================================${NC}"
    echo -e "${RED}✗ FAILURE: Automated tests failed. Please investigate.${NC}"
    echo -e "${RED}=====================================================${NC}"
    exit 1
fi
