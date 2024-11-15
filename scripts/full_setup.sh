#!/bin/bash

# Function to output project information
output_project_info() {
    echo "Project Information"
    echo "===================="

    # Output user and machine information
    echo -e "\nUser and Machine Information"
    echo "-----------------------------"
    echo "User: $(whoami)"
    echo "Hostname: $(hostname)"
    echo "Operating System: $(uname -a)"

    # Output Docker information
    echo -e "\nDocker Information"
    echo "-------------------"
    docker --version
    docker-compose --version

    # Output environment variables
    echo -e "\nEnvironment Variables"
    echo "----------------------"
    echo "GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"
    echo "DB_HOST: $DB_HOST"
    echo "DB_PORT: $DB_PORT"
    echo "DB_NAME: $DB_NAME"
    echo "DB_USER: $DB_USER"
    echo "DB_PASSWORD: ${DB_PASSWORD:0:4}****" # Mask the password for security
    echo "API_KEY: ${API_KEY:0:4}****"         # Mask the API key for security

    # Output Google Cloud information
    echo -e "\nGoogle Cloud Information"
    echo "-------------------------"
    gcloud --version
    echo "Project ID: $(gcloud config get-value project)"

    # Output project structure
    echo -e "\nProject Structure"
    echo "------------------"
    cd ~/TrendAI
    tree -L 2
}

# Function to run the docker setup script
run_docker_setup() {
    echo -e "\nRunning Docker Setup Script"
    echo "----------------------------"
    ~/TrendAI/docker_setup.sh
}

# Main script execution
output_project_info
run_docker_setup
