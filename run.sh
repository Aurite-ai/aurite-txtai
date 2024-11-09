#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory and env file path
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="${SCRIPT_DIR}/.env"

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

# Function to check environment
check_env() {
    load_env
    echo -e "${GREEN}Environment variables loaded from $ENV_FILE${NC}"

    # Only check for service account in local development
    if [ ! -f "${SCRIPT_DIR}/config/service-account.json" ] && [ -z "${GOOGLE_CREDENTIALS}" ]; then
        echo -e "${RED}Warning: No service account credentials found${NC}"
        echo "Either place credentials at config/service-account.json or set GOOGLE_CREDENTIALS"
    fi
}

# Function to manage container
manage_container() {
    local action=$1
    case "$action" in
        "start")
            echo -e "${GREEN}Starting txtai service in Docker container...${NC}"
            docker run \
                --name txtai-container \
                -p 8000:8000 \
                --memory=4g \
                --memory-swap=4g \
                -v "${SCRIPT_DIR}/config":/app/config \
                -v "${SCRIPT_DIR}/data":/app/data \
                -v "${SCRIPT_DIR}/models":/app/models \
                -v "${SCRIPT_DIR}/info":/app/info \
                -e API_KEY="${API_KEY}" \
                -e GOOGLE_CREDENTIALS="${GOOGLE_CREDENTIALS}" \
                txtai-service
            ;;
        "stop")
            echo -e "${GREEN}Stopping txtai service...${NC}"
            docker stop txtai-container
            docker rm txtai-container
            ;;
        "build")
            echo -e "${GREEN}Building txtai service image...${NC}"
            docker build -t txtai-service "${SCRIPT_DIR}"
            ;;
        *)
            echo -e "${RED}Invalid action: $action${NC}"
            echo "Usage: $0 {start|stop|build}"
            exit 1
            ;;
    esac
}

# Main execution
case "$1" in
    "start"|"stop"|"build")
        if [ "$1" != "stop" ]; then
            check_env
        fi
        manage_container "$1"
        ;;
    "restart")
        check_env
        manage_container "stop"
        manage_container "start"
        ;;
    *)
        echo "Usage: $0 {start|stop|build|restart}"
        exit 1
        ;;
esac