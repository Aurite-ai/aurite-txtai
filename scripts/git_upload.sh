#!/bin/bash

PROJECT_ID="trendai-project"
IMAGE_NAME="trendai_app"
TAG="latest"
GCR_IMAGE="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${TAG}"
git add .
git commit -m "Automatic Commit"
git push -u origin main
