#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory and env file path
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="${SCRIPT_DIR}/../.env"

# Allow overriding base URL for Cloud Run testing
BASE_URL=${1:-"http://localhost:8080"}

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

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local data=$3
    local expected_status=${4:-200}

    echo -e "\n${YELLOW}Testing $method $endpoint${NC}"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer ${API_KEY}" \
            "${BASE_URL}${endpoint}")
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            -H "Authorization: Bearer ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${BASE_URL}${endpoint}")
    fi

    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')

    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ Status: $status_code${NC}"
        echo "Response: $response_body"
        return 0
    else
        echo -e "${RED}✗ Expected status $expected_status but got $status_code${NC}"
        echo "Response: $response_body"
        return 1
    fi
}

# Main test execution
main() {
    load_env

    echo -e "${GREEN}Testing txtai API at: $BASE_URL${NC}"

    # Initialize test counters
    total=0
    failed=0

    # Test search endpoint
    ((total++))
    test_endpoint "/search?query=test" || ((failed++))

    # Test add endpoint
    ((total++))
    test_endpoint "/add" "POST" '[{"id": "test1", "text": "This is a test document"}]' || ((failed++))

    # Print summary
    echo -e "\n${GREEN}Test Summary:${NC}"
    echo "Total tests: $total"
    echo -e "Passed: ${GREEN}$((total-failed))${NC}"
    if [ $failed -gt 0 ]; then
        echo -e "Failed: ${RED}$failed${NC}"
        exit 1
    else
        echo -e "\n${GREEN}All tests passed!${NC}"
    fi
}

# Run tests
main