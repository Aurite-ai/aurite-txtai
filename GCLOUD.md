# txtai Cloud Deployment Guide

## Overview

txtai is deployed as a Cloud Run service with the following configuration:

- Memory: 4GB
- CPU: 2 cores
- Port: 8080
- VPC Connector: aurite-vpc-connector
- Service Account: txtai-sa@aurite-dev.iam.gserviceaccount.com

## Prerequisites

- GCP Project: aurite-dev
- Region: us-central1
- Required APIs:
  - Cloud Run
  - Cloud Build
  - Container Registry
  - Secret Manager
  - Storage API

## Infrastructure Components

### Service Account

- Name: txtai-sa@aurite-dev.iam.gserviceaccount.com
- Required Roles:
  - roles/run.invoker
  - roles/storage.objectViewer
  - roles/secretmanager.secretAccessor

### Storage

- GCS Bucket: gs://aurite-txtai-dev/
- Used for storing embeddings index
- Accessible by txtai-sa service account

### Container Registry

- Repository: gcr.io/aurite-dev/txtai
- Built and pushed via Cloud Build

### Cloud Build

- Trigger: txtai-prod
- Source: GitHub repository
- Service Account: cloud-build-service-account@aurite-dev.iam.gserviceaccount.com
- Build Configuration: cloudbuild.yaml

## Deployment Process

1. Build Container:

```bash
# Local build test
docker build -t txtai-service .
```

2. Submit Cloud Build:

```bash
# Using submit_build.sh
./utils/submit_build.sh
```

3. Test Deployment:

```bash
# Get Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe txtai --region=us-central1 --format='value(status.url)')

# Run tests
./utils/test_txtai.sh "$CLOUD_RUN_URL"
```

## Environment Variables

- PORT: 8080 (set in Dockerfile)
- API_KEY: From Secret Manager
- GOOGLE_CREDENTIALS: Service account key from Secret Manager

## Monitoring & Logs

- Cloud Run logs: Available in Cloud Console
- Build logs: Stored in txtai/logs/
- Container logs: Accessible via gcloud logging

## Troubleshooting

1. Port Issues:

   - Container must listen on port 8080
   - Set in Dockerfile and handler.sh

2. Authentication:

   - API requires Bearer token authentication
   - Token must match API_KEY from Secret Manager

3. Service Account:
   - Must have access to GCS bucket
   - Must have access to Secret Manager
   - Must be properly configured in Cloud Run

## Maintenance

1. Update Service:

```bash
# Submit new build
./utils/submit_build.sh
```

2. Check Status:

```bash
# Service status
gcloud run services describe txtai --region=us-central1

# Recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=txtai" --limit=50
```

3. Rollback:

```bash
# List revisions
gcloud run revisions list --service=txtai --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic txtai --to-revision=REVISION_NAME --region=us-central1
```
