#!/bin/bash

# run.sh - Launch script for Manage Digital Ingest Flet application
# This script handles virtual environment setup and app launch

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Manage Digital Ingest - Launcher ===${NC}"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
REQUIREMENTS_FILE="python-requirements.txt"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating .venv...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Check if requirements need to be installed
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    # Check if requirements are already installed
    if ! pip show flet > /dev/null 2>&1; then
        echo -e "${YELLOW}Installing dependencies from $REQUIREMENTS_FILE...${NC}"
        pip install --upgrade pip
        pip install -r "$REQUIREMENTS_FILE"
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    else
        echo -e "${GREEN}✓ Dependencies already installed${NC}"
    fi
else
    echo -e "${RED}Warning: $REQUIREMENTS_FILE not found${NC}"
fi

# Launch the app
echo -e "${GREEN}=== Launching Manage Digital Ingest ===${NC}"
echo ""
flet run app.py

# Deactivate virtual environment on exit
deactivate
