# GCP Configuration Documentation
Generated on: 2024-11-07 20:37:25

## Configuration Overview
- Project ID: aurite-dev
- Region: us-central1
- Service: txtai-service

## Component Status

### Container Images
```bash
$ gcloud container images list --repository=gcr.io/aurite-dev --filter="name:txtai-service"
Listed 0 items.
```

*No container images found in registry - needs to be built and pushed*


### Service Configuration
```bash
$ gcloud run services describe txtai-service --region=us-central1 --format=yaml
ERROR: (gcloud.run.services.describe) Cannot find service [txtai-service]
```

*Service not yet deployed to Cloud Run*


### API Key Secret Configuration
```bash
$ gcloud secrets describe txtai-api-key --format=yaml
createTime: '2024-11-08T00:33:02.767956Z'
etag: '"16265be4ccc354"'
name: projects/422370317143/secrets/txtai-api-key
replication:
  automatic: {}
```

### Bucket Configuration
```bash
$ gsutil ls -L gs://aurite-txtai-dev

```

*Storage bucket not yet created - will be created during deployment*


### Service Account Details
```bash
$ gcloud iam service-accounts describe txtai-sa@aurite-dev.iam.gserviceaccount.com
displayName: txtai Service Account
email: txtai-sa@aurite-dev.iam.gserviceaccount.com
etag: MDEwMjE5MjA=
name: projects/aurite-dev/serviceAccounts/txtai-sa@aurite-dev.iam.gserviceaccount.com
oauth2ClientId: '108666060544198990418'
projectId: aurite-dev
uniqueId: '108666060544198990418'
```

## Configuration Issues
- ❌ Container image not found in GCR (gcr.io/aurite-dev/txtai-service)
- ❌ Missing required Docker configuration files
- ❌ Cloud Run service not deployed
- ❌ Storage bucket not configured
- ❌ Build trigger missing API_KEY substitution
- ❌ cloudbuild.yaml not found in mobile-server directory

## Required Actions

### 1. Build and Push Container
```bash
docker build -t gcr.io/aurite-dev/txtai-service ./txtai
docker push gcr.io/aurite-dev/txtai-service
```

### Deploy to Cloud Run
```bash
gcloud run deploy txtai-service \
  --image gcr.io/aurite-dev/txtai-service \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --service-account txtai-sa@aurite-dev.iam.gserviceaccount.com \
  --set-env-vars API_KEY=$(gcloud secrets versions access latest --secret=txtai-api-key)
```
