#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Get the API URL from Cloud Run
API_URL=$(gcloud run services describe txtai-service --platform managed --region us-central1 --format 'value(status.url)')
if [ -z "$API_URL" ]; then
    echo -e "${RED}Error: Could not get service URL${NC}"
    exit 1
fi

# Get API key from secret manager
API_KEY=$(gcloud secrets versions access latest --secret=txtai-api-key)
if [ -z "$API_KEY" ]; then
    echo -e "${RED}Error: Could not get API key${NC}"
    exit 1
fi

echo "Testing txtai API authentication..."

# Test with API key
echo -e "\n${GREEN}Testing with valid API key:${NC}"
curl -s -w "\n%{http_code}" "${API_URL}/count" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json"

# Test without API key (should fail)
echo -e "\n${GREEN}Testing without API key (should fail):${NC}"
curl -s -w "\n%{http_code}" "${API_URL}/count" \
  -H "Content-Type: application/json"