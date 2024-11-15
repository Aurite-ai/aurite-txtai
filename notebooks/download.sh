#!/bin/bash
    
# Create examples directory if it doesn't exist
mkdir -p info/examples

# GitHub API token from environment
if [ -n "$GITHUB_TOKEN" ]; then
    AUTH_HEADER="Authorization: token $GITHUB_TOKEN"
else
    AUTH_HEADER="Accept: application/vnd.github.v3+json"
fi

# Download all example notebooks
echo "Fetching txtai examples list..."
curl -s -L -H "$AUTH_HEADER" "https://api.github.com/repos/neuml/txtai/contents/examples?per_page=100" | \
  grep "\"download_url\".*ipynb" | \
  cut -d '"' -f 4 | \
  while IFS= read -r url; do
    filename=$(basename "$url")
    echo "Downloading $filename..."
    curl -s -L "$url" -o "info/examples/$filename"
    sleep 1 # Rate limiting protection
  done

echo "Download complete. Examples saved to info/examples/"