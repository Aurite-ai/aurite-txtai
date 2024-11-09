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
BUILD_LOG="${LOG_DIR}/build_$(date +%Y%m%d_%H%M%S).log"

# Ensure logs directory exists
mkdir -p "$LOG_DIR"

# Clean up old logs - keep only 5 most recent
cd "$LOG_DIR"
ls -t build_*.log | tail -n +6 | xargs -I {} rm -- {}
cd - > /dev/null

echo "Starting cloud build submission..."
echo "Logs will be written to: $BUILD_LOG"

# Change to the root directory where cloudbuild.yaml is located
cd "$ROOT_DIR"

# Submit build and capture build ID with better parsing
BUILD_OUTPUT=$(gcloud builds submit --config=cloudbuild.yaml 2>&1 | tee -a "$BUILD_LOG")
BUILD_ID=$(echo "$BUILD_OUTPUT" | grep -o 'projects/.*/locations/.*/builds/[a-z0-9-]*' | cut -d'/' -f6)

if [ -z "$BUILD_ID" ]; then
    echo -e "${RED}Failed to get build ID${NC}"
    echo "Build output:"
    echo "$BUILD_OUTPUT"
    exit 1
fi

echo -e "${GREEN}Build submitted with ID: $BUILD_ID${NC}"
echo -e "${YELLOW}Streaming logs...${NC}"

# Stream logs until build completes
gcloud builds log --stream "$BUILD_ID" 2>&1 | tee -a "$BUILD_LOG"

# Check build status
STATUS=$(gcloud builds describe "$BUILD_ID" --format="get(status)")

echo -e "\nBuild completed with status: ${STATUS}"
echo "Full logs available at: $BUILD_LOG"

# Copy logs to GCS (only if build was successful)
if [ "$STATUS" = "SUCCESS" ]; then
    echo "Copying logs to GCS..."
    gsutil cp "$BUILD_LOG" "gs://aurite-txtai-dev/logs/"
fi

if [ "$STATUS" != "SUCCESS" ]; then
    echo -e "${RED}Build failed. Check logs for details.${NC}"
    exit 1
fi