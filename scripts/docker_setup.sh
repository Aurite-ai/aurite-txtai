#!/bin/bash
export PROJECT_ID=trendai-project

# Function to check if the user is in the docker group
check_docker_group() {
    if groups $USER | grep &>/dev/null '\bdocker\b'; then
        echo "User is already in the docker group."
    else
        echo "User is not in the docker group. Adding user to docker group..."
        sudo usermod -aG docker $USER
        echo "User added to docker group. Please log out and log back in or restart your shell session."
        exit 1
    fi
}

# Function to set permissions for Docker socket
set_docker_socket_permissions() {
    echo "Setting permissions for Docker socket..."
    sudo chmod 666 /var/run/docker.sock
}

# Function to export environment variables from Google Cloud Secret Manager
export_env_variables() {
    echo "Exporting environment variables..."
    export DB_PASSWORD=$(gcloud secrets versions access latest --secret="trendai-db-password")
    if [ -z "$DB_PASSWORD" ]; then
        echo "Error: DB_PASSWORD is not set. Exiting..."
        exit 1
    else
        echo "DB_PASSWORD successfully retrieved."
    fi

    export API_KEY=$(gcloud secrets versions access latest --secret="trendai-api-key")
    if [ -z "$API_KEY" ]; then
        echo "Error: API_KEY is not set. Exiting..."
        exit 1
    else
        echo "API_KEY successfully retrieved."
    fi
}

# Function to clean up Docker environment
cleanup_docker() {
    echo "Cleaning up Docker environment..."
    docker-compose down
    docker system prune --volumes -f
    docker network prune -f
}

# Function to run Docker Compose
run_docker_compose() {
    echo "Running Docker Compose..."
    docker-compose build --no-cache
    docker-compose up --build -d
}

# Function to test routes with retries
test_routes() {
    INTERNAL_URL="https://127.0.0.1:443/health"
    EXTERNAL_IP=$(curl -s http://checkip.amazonaws.com)
    EXTERNAL_URL="https://$EXTERNAL_IP:443/health"

    # Add a delay to ensure the application has started
    echo "Waiting for the application to start..."
    sleep 30

    for i in {1..5}; do
        echo "Testing internal route: $INTERNAL_URL (Attempt $i)"
        INTERNAL_RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" $INTERNAL_URL)
        if [ "$INTERNAL_RESPONSE" -eq 200 ]; then
            echo "Internal route is accessible."
            break
        else
            echo "Failed to access internal route. Response code: $INTERNAL_RESPONSE"
            sleep 5
        fi
    done

    for i in {1..5}; do
        echo "Testing external route: $EXTERNAL_URL (Attempt $i)"
        EXTERNAL_RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" $EXTERNAL_URL)
        if [ "$EXTERNAL_RESPONSE" -eq 200 ]; then
            echo "External route is accessible."
            break
        else
            echo "Failed to access external route. Response code: $EXTERNAL_RESPONSE"
            sleep 5
        fi
    done
}

# Function to test the new trends routes
test_trends_routes() {
    INTERNAL_TRENDS_URL="https://127.0.0.1:443/trends"
    INTERNAL_SPORTS_TRENDS_URL="https://127.0.0.1:443/trends/sports"
    EXTERNAL_IP=$(curl -s http://checkip.amazonaws.com)
    EXTERNAL_TRENDS_URL="https://$EXTERNAL_IP:443/trends"
    EXTERNAL_SPORTS_TRENDS_URL="https://$EXTERNAL_IP:443/trends/sports"

    # Add a delay to ensure the application has started
    echo "Waiting for the application to start..."
    sleep 10

    for i in {1..5}; do
        echo "Testing internal trends route: $INTERNAL_TRENDS_URL (Attempt $i)"
        INTERNAL_RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" $INTERNAL_TRENDS_URL)
        if [ "$INTERNAL_RESPONSE" -eq 200 ]; then
            echo "Internal trends route is accessible."
            break
        else
            echo "Failed to access internal trends route. Response code: $INTERNAL_RESPONSE"
            curl -k -v -H "X-API-Key: $API_KEY" $INTERNAL_TRENDS_URL # Verbose output for diagnostic
            sleep 5
        fi
    done

    for i in {1..5}; do
        echo "Testing internal sports trends route: $INTERNAL_SPORTS_TRENDS_URL (Attempt $i)"
        INTERNAL_RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" $INTERNAL_SPORTS_TRENDS_URL)
        if [ "$INTERNAL_RESPONSE" -eq 200 ]; then
            echo "Internal sports trends route is accessible."
            break
        else
            echo "Failed to access internal sports trends route. Response code: $INTERNAL_RESPONSE"
            curl -k -v -H "X-API-Key: $API_KEY" $INTERNAL_SPORTS_TRENDS_URL # Verbose output for diagnostic
            sleep 5
        fi
    done

    for i in {1..5}; do
        echo "Testing external trends route: $EXTERNAL_TRENDS_URL (Attempt $i)"
        EXTERNAL_RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" $EXTERNAL_TRENDS_URL)
        if [ "$EXTERNAL_RESPONSE" -eq 200 ]; then
            echo "External trends route is accessible."
            break
        else
            echo "Failed to access external trends route. Response code: $EXTERNAL_RESPONSE"
            curl -k -v -H "X-API-Key: $API_KEY" $EXTERNAL_TRENDS_URL # Verbose output for diagnostic
            sleep 5
        fi
    done

    for i in {1..5}; do
        echo "Testing external sports trends route: $EXTERNAL_SPORTS_TRENDS_URL (Attempt $i)"
        EXTERNAL_RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" $EXTERNAL_SPORTS_TRENDS_URL)
        if [ "$EXTERNAL_RESPONSE" -eq 200 ]; then
            echo "External sports trends route is accessible."
            break
        else
            echo "Failed to access external sports trends route. Response code: $EXTERNAL_RESPONSE"
            curl -k -v -H "X-API-Key: $API_KEY" $EXTERNAL_SPORTS_TRENDS_URL # Verbose output for diagnostic
            sleep 5
        fi
    done
}

# Main script execution

check_docker_group
set_docker_socket_permissions
export_env_variables
cleanup_docker
run_docker_compose

# Wait a bit for the application to start
sleep 10

test_routes
test_trends_routes
python test_trends.py

# Clean up
# cleanup_docker
