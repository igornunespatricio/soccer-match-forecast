#!/bin/bash

# Script to generate markdown file from project tree structure
# Usage: ./generate_markdown_tree.sh [output_file.md]

# Default output file
OUTPUT_FILE="${1:-PROJECT_STRUCTURE.md}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if tree command is available
if ! command -v tree &> /dev/null; then
    echo -e "${RED}Error: tree command not found. Installing...${NC}"
    sudo apt update && sudo apt install -y tree
fi

# Get project root directory name for title
PROJECT_NAME=$(basename "$(pwd)")

# Generate the markdown content
echo -e "${BLUE}Generating markdown structure for: $PROJECT_NAME${NC}"

{
    # Markdown header
    echo "# Project Structure: $PROJECT_NAME"
    echo ""
    echo "\`\`\`"
    
    # Generate tree structure (exclude common cache/files)
    tree -a -I '__pycache__|*.pyc|*.db-*|.git|.venv|.vscode|.idea' --dirsfirst
    
    # Close code block
    echo "\`\`\`"
    echo ""
    
    # Add timestamp
    echo "***"
    echo "*Generated on: $(date)*"
    echo "*Using: \`tree -a -I '__pycache__|*.pyc|*.db-*|.git|.venv|.vscode|.idea' --dirsfirst\`*"
    
} > "$OUTPUT_FILE"

echo -e "${GREEN}Markdown file generated: $OUTPUT_FILE${NC}"
echo -e "${BLUE}Total lines written: $(wc -l < "$OUTPUT_FILE")${NC}"