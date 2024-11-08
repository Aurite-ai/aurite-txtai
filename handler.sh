#!/bin/bash

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check config file
check_config() {
    local config_file=$1
    if [ ! -f "$config_file" ]; then
        echo "Error: No config file found at $config_file"
        return 1
    fi

    # Validate config using yq
    if ! yq eval '.' "$config_file" > /dev/null 2>&1; then
        echo "Error: Invalid YAML in config file"
        return 1
    fi
    return 0
}

# Function to start server
start_server() {
    local config_file=$1
    local creds_file=$2
    local port=${PORT:-8000}

    export PYTHONUNBUFFERED=1
    if [ -f "$creds_file" ]; then
        export GOOGLE_APPLICATION_CREDENTIALS="$creds_file"
    fi

    # Ensure API key is set
    if [ -z "${API_KEY}" ]; then
        echo "Error: API_KEY environment variable not set"
        exit 1
    fi

    CONFIG="$config_file" uvicorn "txtai.api:app" \
        --host 0.0.0.0 \
        --port "$port" \
        --log-level debug \
        --timeout-keep-alive 75
}

# Function to check health
check_health() {
    curl -f http://localhost:${PORT:-8000}/health 2>/dev/null
    return $?
}

# Main execution
if [ "$1" = "stop" ]; then
    echo "Stopping txtai API service..."
    docker stop txtai-container
    docker rm txtai-container
    exit 0
fi

# Restart
if [ "$1" = "restart" ]; then
    $0 stop
    $0
    exit 0
fi

# Start For Docker Container
if [ -f /.dockerenv ]; then
    echo "Starting txtai API service inside container..."
    CONFIG_FILE="/app/config.yml"
    CREDS_FILE="/app/service-account.json"

    if check_config "$CONFIG_FILE"; then
        start_server "$CONFIG_FILE" "$CREDS_FILE" &

        # Wait for server to be healthy
        echo "Waiting for server to be healthy..."
        for i in {1..30}; do
            if check_health; then
                echo "Server is healthy"
                break
            fi
            sleep 1
        done

        # Keep container running
        wait
    else
        exit 1
    fi
else
    # Start For Local Development
    echo "Starting txtai API service in Docker container..."
    docker stop txtai-container || true
    docker rm txtai-container || true

    if docker build -t txtai-service "${SCRIPT_DIR}"; then
        docker run \
            --name txtai-container \
            -p 8000:8000 \
            --memory=4g \
            --memory-swap=4g \
            -v "${SCRIPT_DIR}/services/txtai/data":/app/data \
            -v "${SCRIPT_DIR}/services/txtai/models":/app/models \
            -v "${SCRIPT_DIR}/services/txtai/info":/app/info \
            txtai-service
    else
        echo "Error: Docker build failed"
        exit 1
    fi
fi