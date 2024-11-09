#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${ROOT_DIR}/logs"
CLOUDBUILD_LOG="${ROOT_DIR}/cloudbuild.log"
BUILD_LOG="${LOG_DIR}/build_$(date +%Y%m%d_%H%M%S).log"
CLOUDBUILD_YAML="${ROOT_DIR}/cloudbuild.yaml"

# Ensure logs directory exists
mkdir -p "$LOG_DIR"

# Initialize or clear cloudbuild.log
echo "Build started at $(date)" > "$CLOUDBUILD_LOG"

# Function to log message to both console and logs
log_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}" | tee -a "$CLOUDBUILD_LOG"
}

# Function to capture build logs
capture_build_logs() {
    local build_id=$1
    log_message "$YELLOW" "Fetching build logs..."

    # Get full build logs
    gcloud builds log "$build_id" --format='value(status,logUrl,steps.status,steps.timing)' 2>&1 | tee -a "$CLOUDBUILD_LOG"

    # Get detailed step logs
    gcloud builds log "$build_id" --format='value(steps.logs)' 2>&1 | tee -a "$CLOUDBUILD_LOG"
}

# Function to get Cloud Run logs
get_cloud_run_logs() {
    local service_name=$1
    local revision_name=$2

    echo -e "${YELLOW}Fetching Cloud Run container logs...${NC}"

    # Get logs for the revision
    gcloud logging read "resource.type=cloud_run_revision AND \
        resource.labels.service_name=$service_name AND \
        resource.labels.revision_name=$revision_name" \
        --project=aurite-dev \
        --format='value(textPayload)' \
        --limit=50 2>&1 | tee -a "$BUILD_LOG"
}

log_message "$BLUE" "Starting cloud build submission..."
log_message "$BLUE" "Using cloudbuild.yaml at: $CLOUDBUILD_YAML"

# Verify cloudbuild.yaml exists
if [ ! -f "$CLOUDBUILD_YAML" ]; then
    log_message "$RED" "Error: cloudbuild.yaml not found at $CLOUDBUILD_YAML"
    exit 1
fi

# Change to the root directory where cloudbuild.yaml is located
cd "$ROOT_DIR" || exit 1

# Submit build and capture build ID
log_message "$YELLOW" "Submitting build..."
BUILD_OUTPUT=$(gcloud beta builds submit --config="$CLOUDBUILD_YAML" . 2>&1 | tee -a "$CLOUDBUILD_LOG")
BUILD_ID=$(echo "$BUILD_OUTPUT" | grep -o 'builds/[a-z0-9-]*' | cut -d'/' -f2 | head -n1)

if [ -z "$BUILD_ID" ]; then
    log_message "$RED" "Failed to get build ID"
    log_message "$RED" "Build output:"
    echo "$BUILD_OUTPUT" | tee -a "$CLOUDBUILD_LOG"
    exit 1
fi

log_message "$GREEN" "Build submitted with ID: $BUILD_ID"

# Stream and capture logs
log_message "$YELLOW" "Streaming build logs..."
gcloud builds log --stream "$BUILD_ID" 2>&1 | tee -a "$CLOUDBUILD_LOG"

# Get final build status
STATUS=$(gcloud builds describe "$BUILD_ID" --format="get(status)")
log_message "$BLUE" "Build completed with status: ${STATUS}"

# Capture detailed logs
capture_build_logs "$BUILD_ID"

# Save final log file
cp "$CLOUDBUILD_LOG" "$BUILD_LOG"
log_message "$GREEN" "Build log saved to: $BUILD_LOG"

if [ "$STATUS" != "SUCCESS" ]; then
    log_message "$RED" "Build failed. Check logs for details."

    # Extract revision name from error message
    REVISION_NAME=$(echo "$BUILD_OUTPUT" | grep -o "Revision '[^']*'" | cut -d"'" -f2)

    if [ -n "$REVISION_NAME" ]; then
        get_cloud_run_logs "txtai" "$REVISION_NAME"
    fi

    log_message "$YELLOW" "Last few lines of build log:"
    tail -n 20 "$BUILD_LOG"
    exit 1
fi

# Success message
log_message "$GREEN" "Build completed successfully!"