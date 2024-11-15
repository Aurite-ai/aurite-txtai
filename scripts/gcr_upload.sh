#!/bin/bash

PROJECT_ID="trendai-project"
IMAGE_NAME="trendai_app"
TAG="latest"
GCR_IMAGE="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${TAG}"

# Authenticate with Google Cloud
# gcloud auth login
gcloud config set project $PROJECT_ID

# Enable necessary services
gcloud services enable containerregistry.googleapis.com

# Build the Docker image
docker build -t $IMAGE_NAME .

# Tag the Docker image
docker tag $IMAGE_NAME $GCR_IMAGE

# Push the Docker image to GCR
docker push $GCR_IMAGE

# Verify the image
gcloud container images list
