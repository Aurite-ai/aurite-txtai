#!/bin/bash

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to setup service account
setup_service_account() {
    # Skip service account setup for local development
    if [ -z "$GOOGLE_CREDENTIALS" ] && [ ! -f "/app/config/service-account.json" ]; then
        echo "Running in local mode without GCP credentials"
        return 0
    fi

    if [ -n "$GOOGLE_CREDENTIALS" ]; then
        echo "Using service account credentials from environment"
        echo "$GOOGLE_CREDENTIALS" > /app/config/service-account.json
        export GOOGLE_APPLICATION_CREDENTIALS="/app/config/service-account.json"
    elif [ -f "/app/config/service-account.json" ]; then
        echo "Using service account credentials from mounted file"
        export GOOGLE_APPLICATION_CREDENTIALS="/app/config/service-account.json"
    fi
}

# Function to check config file
check_config() {
    local config_file=$1
    if [ ! -f "$config_file" ]; then
        echo "Error: No config file found at $config_file"
        return 1
    fi

    if ! yq eval '.' "$config_file" > /dev/null 2>&1; then
        echo "Error: Invalid YAML in config file"
        return 1
    fi
    return 0
}

# Function to start server
start_server() {
    local config_file=$1
    local port=${PORT:-8080}

    export PYTHONUNBUFFERED=1

    # Setup service account credentials
    setup_service_account

    echo "Starting server on port $port"
    CONFIG="$config_file" uvicorn "txtai.api:app" \
        --host 0.0.0.0 \
        --port "$port" \
        --log-level debug \
        --timeout-keep-alive 75
}

# Main execution
CONFIG_FILE="/app/config/config.yml"

if check_config "$CONFIG_FILE"; then
    start_server "$CONFIG_FILE"
else
    exit 1
fi