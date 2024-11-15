#!/bin/bash

# Set up variables
SSD_PATH="/mnt/disks/ssd"
TXTAI_DIR="$SSD_PATH/txtai-service"
CONFIG_FILE="$TXTAI_DIR/config/config.yml"
DOCKER_COMPOSE_FILE="$TXTAI_DIR/docker-compose.yml"
LOG_FILE="$TXTAI_DIR/txtai.log"

# Function to log messages
log_message() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check if txtai is running
is_txtai_running() {
  docker-compose logs txtai | grep -q "Application startup complete"
}

# Function to stop and remove existing txtai containers
stop_and_remove_txtai() {
  log_message "Stopping and removing existing txtai containers..."
  cd "$TXTAI_DIR" || exit
  docker-compose down
  docker stop "$(docker ps -q --filter name=txtai)" 2>/dev/null
  docker rm "$(docker ps -aq --filter name=txtai)" 2>/dev/null
  docker volume prune -f
}

# Create necessary directories
create_directories() {
  sudo mkdir -p "$TXTAI_DIR/config"
  sudo chown -R "$(id -u):$(id -g)" "$TXTAI_DIR"
  log_message "Created necessary directories"
}

# Create config file
create_config_file() {
  cat <<'CONFIG' >"$CONFIG_FILE"
# Index file path
path: /config/index

# Allow indexing of documents
writable: true

# Embeddings index
embeddings:
  path: sentence-transformers/all-MiniLM-L6-v2
  content: true

# Text summarization
summary:
  path: facebook/bart-large-cnn

# Similarity
similarity:

# Zero-shot labeling
labels:
  path: facebook/bart-large-mnli

CONFIG
  log_message "Created optimized config file"
}

# Create docker-compose file
create_docker_compose_file() {
  cat <<DOCKER >"$DOCKER_COMPOSE_FILE"
version: '3'
services:
  txtai:
    image: neuml/txtai-cpu
    ports:
      - "8000:8000"
    volumes:
      - $TXTAI_DIR/config:/config
    environment:
      - CONFIG=/config/config.yml
    command: ["uvicorn", "txtai.api:app", "--host", "0.0.0.0", "--port", "8000"]
    deploy:
      resources:
        limits:
          cpus: '6'
          memory: 24G
DOCKER
  log_message "Created docker-compose file with optimized resource limits"
}

# Start txtai service
start_txtai() {
  cd "$TXTAI_DIR" || exit
  docker-compose up -d
  log_message "Started txtai service"
}

# Main execution
main() {
  log_message "Starting txtai setup"

  stop_and_remove_txtai
  create_directories
  create_config_file
  create_docker_compose_file
  start_txtai

  # Wait for the service to start
  log_message "Waiting for txtai service to start..."
  for i in {1..60}; do
    if is_txtai_running; then
      log_message "txtai service is running on port 8000"
      exit 0
    fi
    sleep 5
    if [ $((i % 12)) -eq 0 ]; then
      log_message "Still waiting for txtai service to start... ($((i / 12)) minutes)"
    fi
  done

  log_message "Error: txtai service failed to start. Check docker logs for more information."
  log_message "Showing Docker logs:"
  docker-compose logs
  exit 1
}

# Run the main function
main
