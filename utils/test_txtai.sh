#!/bin/bash

# Get script directory and env file path
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="${SCRIPT_DIR}/../.env"
BASE_URL="http://localhost:8000"

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

# Update the check_env function
check_env() {
    load_env
    echo -e "${GREEN}Environment variables loaded from $ENV_FILE${NC}"
}

echo "Testing txtai API endpoints..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

# Check and install required dependencies
check_dependencies() {
    # Check for jq
    if ! command -v jq &> /dev/null; then
        echo "jq is not installed. Installing..."
        sudo apt-get update && sudo apt-get install -y jq
    fi

    # Check for curl
    if ! command -v curl &> /dev/null; then
        echo "curl is not installed. Installing..."
        sudo apt-get update && sudo apt-get install -y curl
    fi
}

# Check if server is running
check_server() {
    echo "Checking if txtai server is running..."
    if ! curl -s \
        -H "Authorization: Bearer ${API_KEY}" \
        "${BASE_URL}/openapi.json" > /dev/null; then
        echo -e "${RED}Error: txtai server is not running at ${BASE_URL}${NC}"
        echo "Please start the server using the run.sh script first"
        exit 1
    fi
    echo -e "${GREEN}Server is running!${NC}"
}

# Helper function for formatting JSON output
format_json() {
    local json=$1
    local endpoint=$2
    local max_items=10

    # Add colors to numeric values and strings
    local JQ_COLORS="1;36:0;33:0;37:0;37:0;37:1;37:1;32"  # Cyan for numbers, yellow for strings

    # Handle vector responses differently
    if [[ "$endpoint" == *"transform"* ]]; then
        # For transform endpoints, truncate the vector output
        echo "$json" | jq --color-output 'if type == "array" and (length > 10) then
            (.[0:5] + ["..."] + .[-5:])
        else
            .
        end'
    else
        # For other endpoints, show full response
        echo "$json" | jq --color-output '.'
    fi
}

# Test data
TEST_DOCS='[
    {"text": "txtai is an AI-powered search engine", "id": "doc1"},
    {"text": "txtai supports semantic search capabilities", "id": "doc2"},
    {"text": "Vector search is fast and efficient", "id": "doc3"}
]'

# Validation function
validate_response() {
    local endpoint=$1
    local response=$2
    local expected_type=$3

    case "$expected_type" in
        "count")
            if ! echo "$response" | jq -e 'type=="number"' > /dev/null; then
                echo -e "${RED}Error: Expected number response from ${endpoint}${NC}"
                return 1
            fi
            ;;
        "search")
            case "$endpoint" in
                "/batchsearch")
                    # Handle nested array response for batch search
                    if ! echo "$response" | jq -e 'type=="array" and all(type=="array") and all(.[]; all(has("id") and has("score")))' > /dev/null; then
                        echo -e "${RED}Error: Invalid batch search response format from ${endpoint}${NC}"
                        return 1
                    fi
                    ;;
                *)
                    # Handle single array response for regular search
                    if ! echo "$response" | jq -e 'type=="array" and all(has("id") and has("score"))' > /dev/null; then
                        echo -e "${RED}Error: Invalid search response format from ${endpoint}${NC}"
                        return 1
                    fi
                    ;;
            esac
            ;;
        "vector")
            case "$endpoint" in
                "/batchtransform")
                    # Handle array of vectors
                    if ! echo "$response" | jq -e 'type=="array" and all(type=="array" and all(type=="number"))' > /dev/null; then
                        echo -e "${RED}Error: Invalid batch vector response from ${endpoint}${NC}"
                        return 1
                    fi
                    ;;
                *)
                    # Handle single vector
                    if ! echo "$response" | jq -e 'type=="array" and all(type=="number")' > /dev/null; then
                        echo -e "${RED}Error: Invalid vector response from ${endpoint}${NC}"
                        return 1
                    fi
                    ;;
            esac
            ;;
        "delete")
            if ! echo "$response" | jq -e 'type=="array" and all(type=="string")' > /dev/null; then
                echo -e "${RED}Error: Invalid delete response format from ${endpoint}${NC}"
                return 1
            fi
            ;;
        *)
            return 0
            ;;
    esac
    return 0
}

# Test function with proper error handling and logging
test_endpoint() {
    local endpoint=$1
    local method=$2
    local data=$3
    local description=$4
    local params=$5
    local expected_type=$6

    echo -e "\n${GREEN}Testing ${method} ${endpoint}${NC}"
    echo "Description: ${description}"

    local start_time=$(date +%s.%N)

    if [[ ! -z "$data" ]]; then
        echo "Request:"
        format_json "$data" "$endpoint"
    fi

    local response
    local status
    if [[ "$method" == "GET" ]]; then
        response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer ${API_KEY}" \
            "${BASE_URL}${endpoint}${params:+?}${params}")
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X "${method}" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${API_KEY}" \
            "${BASE_URL}${endpoint}" \
            -d "${data}")
    fi

    status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [[ "$status" == "200" ]]; then
        echo -e "${GREEN}Status: ${status}${NC}"
        if [[ ! -z "$body" ]]; then
            echo "Response:"
            format_json "$body" "$endpoint"

            if [[ ! -z "$expected_type" ]]; then
                validate_response "$endpoint" "$body" "$expected_type"
            fi
        else
            echo "Response: <empty response - success>"
        fi
    else
        echo -e "${RED}Error: Status ${status}${NC}"
        echo "Response:"
        format_json "$body" "$endpoint"
        return 1
    fi

    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)
    # Color timing based on duration
    if (( $(echo "$duration < 0.1" | bc -l) )); then
        echo -e "Time: ${GREEN}${duration}s${NC}"
    elif (( $(echo "$duration < 0.5" | bc -l) )); then
        echo -e "Time: ${YELLOW}${duration}s${NC}"
    else
        echo -e "Time: ${RED}${duration}s${NC}"
    fi
    echo "----------------------------------------"
}

# Update test sequence
test_sequence() {
    # Initial count
    test_endpoint "/count" "GET" "" "Get initial document count" "" "count"

    # Add documents
    test_endpoint "/add" "POST" "$TEST_DOCS" "Add test documents" "" "null"

    # Build index
    test_endpoint "/index" "GET" "" "Build search index" "" "null"

    # Verify count
    test_endpoint "/count" "GET" "" "Verify document count" "" "count"

    # Test search
    test_endpoint "/search" "GET" "" "Search documents" "query=what%20is%20txtai" "search"

    # Test batch operations
    test_endpoint "/batchsearch" "POST" '{
        "queries": ["what is txtai", "semantic search"],
        "limit": 2
    }' "Batch search documents" "" "search"

    # Test vector operations
    test_endpoint "/transform" "GET" "" "Transform text to vector" "text=AI%20powered%20search" "vector"

    # Test cleanup
    test_endpoint "/delete" "POST" '["doc1", "doc2", "doc3"]' "Delete test documents" "" "delete"

    # Verify cleanup
    test_endpoint "/count" "GET" "" "Verify cleanup" "" "count"
}

# Run tests
main() {
    local failed=0
    local total=9

    check_dependencies
    check_env
    check_server

    echo "Starting API tests..."
    echo -e "\n${GREEN}Running Tests:${NC}"
    echo "- Basic Operations (count, add, index): 3 tests"
    echo "- Search Operations (search, batchsearch): 2 tests"
    echo "- Vector Operations (transform): 1 test"
    echo "- Cleanup Operations (delete, verify): 2 tests"

    if test_sequence; then
        failed=0
    else
        failed=1
    fi

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

main