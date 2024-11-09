#!/bin/bash

# Update the environment loading section at the top of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="${SCRIPT_DIR}/../.env"
DOC_FILE="${SCRIPT_DIR}/../api_documentation.md"
BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to load environment variables
load_env() {
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}Error: .env file not found at $ENV_FILE${NC}"
        exit 1
    fi

    # Source the environment variables
    set -a
    source "$ENV_FILE"
    set +a

    # Validate required variables
    if [ -z "${API_KEY}" ]; then
        echo -e "${RED}Error: API_KEY environment variable not set${NC}"
        echo "Please ensure API_KEY is set in .env"
        exit 1
    fi
}

# Check server status
check_server() {
    echo "Checking if txtai server is running..."
    if ! curl -s \
        -H "Authorization: Bearer ${API_KEY}" \
        "${BASE_URL}/openapi.json" > /dev/null; then
        echo -e "${RED}Error: txtai server is not running at ${BASE_URL}${NC}"
        echo "Please start the server using run.sh first"
        exit 1
    fi
    echo -e "${GREEN}Server is running!${NC}"
}

# Update main() to use load_env
main() {
    load_env
    check_server

    # Get OpenAPI spec once
    local spec=$(curl -s -H "Authorization: Bearer ${API_KEY}" "${BASE_URL}/openapi.json")

    # Rest of the main function remains the same...
}

# Call main function
main

echo "API documentation has been saved to ${DOC_FILE}"