# GCP Configuration Documentation

## Project Details

- Project ID: `aurite-dev`
- Project Number: `422370317143`
- Region: `us-central1`

## Service Accounts

Currently configured service accounts:

- ✅ `txtai-sa@aurite-dev.iam.gserviceaccount.com`

  - Used for all service deployments and triggers
  - Roles:
    - roles/run.invoker
    - roles/run.serviceAgent
    - roles/storage.objectCreator
    - roles/storage.objectViewer
    - roles/secretmanager.secretAccessor
    - roles/run.admin

  ```bash
  # List roles
  gcloud projects get-iam-policy aurite-dev \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:serviceAccount:txtai-sa@aurite-dev.iam.gserviceaccount.com"

  # Grant new role
  gcloud projects add-iam-policy-binding aurite-dev \
    --member="serviceAccount:txtai-sa@aurite-dev.iam.gserviceaccount.com" \
    --role="ROLE_NAME"
  ```

## Storage

- ✅ Bucket: `gs://aurite-txtai-dev/` exists

  ```bash
  # List bucket contents
  gsutil ls gs://aurite-txtai-dev/

  # Grant access
  gsutil iam ch serviceAccount:txtai-sa@aurite-dev.iam.gserviceaccount.com:objectViewer gs://aurite-txtai-dev
  ```

## Database

- ✅ Cloud SQL instance: `aurite-postgres`
  - Version: POSTGRES_13
  - Location: us-central1-c
  - Tier: db-custom-1-3840
  - Public IP: 34.29.147.157

```bash
# List instances
gcloud sql instances list

# Get connection info
gcloud sql instances describe aurite-postgres \
    --format="table(connectionName,ipAddresses)"
```

## Cache

- ✅ Redis instance: `aurite-redis`
  - Version: REDIS_6_X
  - Region: us-central1
  - Tier: BASIC
  - Size: 1GB
  - Host: 10.28.157.227
  - Port: 6379

```bash
# List instances
gcloud redis instances list --region=us-central1

# Get instance details
gcloud redis instances describe aurite-redis --region=us-central1
```

## Secrets

Required secrets:

- ❌ `API_KEY`
- ✅ `txtai-sa-key` exists

```bash
# List secrets
gcloud secrets list

# Create new secret
gcloud secrets create SECRET_NAME \
    --replication-policy="automatic"

# Add secret version
echo "secret-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding SECRET_NAME \
    --member="serviceAccount:txtai-sa@aurite-dev.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Cloud Run

Current services:

- ❌ txtai service not deployed
- ✅ mobile-server deployed at https://mobile-server-422370317143.us-central1.run.app
- ❌ persona-server not deployed

```bash
# List services
gcloud run services list --platform managed --region us-central1

# Deploy new service
gcloud run deploy SERVICE_NAME \
    --source . \
    --region=us-central1 \
    --service-account=txtai-sa@aurite-dev.iam.gserviceaccount.com \
    --memory=4Gi \
    --cpu=2 \
    --port=8000

# Get service URL
gcloud run services describe SERVICE_NAME \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)'
```

## Cloud Build

Triggers configured:

- ✅ `txtai-prod` (ID: 2aeed79f-0651-4a44-9f68-0a103679ffbc)
  - Branch trigger: `^main$`
  - Using service account: txtai-sa@aurite-dev.iam.gserviceaccount.com
  - Repository: Aurite-ai-aurite-txtai
  - Substitutions:
    - \_API_KEY: $(gcloud secrets versions access latest --secret=API_KEY)
    - \_SA_KEY: $(gcloud secrets versions access latest --secret=txtai-sa-key)
  - Requires approval: true
  - Build logs: Included with status
  - Tags: txtai

```bash
# List triggers
gcloud builds triggers list --region=us-central1

# Get trigger details
gcloud builds triggers describe 2aeed79f-0651-4a44-9f68-0a103679ffbc --region=us-central1

# List recent builds
gcloud builds list --region=us-central1 --limit=5

# View build logs
gcloud builds log BUILD_ID

# Submit manual build
gcloud builds submit --config=cloudbuild.yaml
```

## Required Actions

### 1. Create API_KEY Secret

```bash
# Create secret
echo "your-api-key" | gcloud secrets create API_KEY \
    --data-file=- \
    --replication-policy="automatic"

# Grant access to txtai-sa
gcloud secrets add-iam-policy-binding API_KEY \
    --member="serviceAccount:txtai-sa@aurite-dev.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 2. Deploy txtai Service

```bash
# Deploy service
gcloud run deploy txtai \
    --source . \
    --region=us-central1 \
    --service-account=txtai-sa@aurite-dev.iam.gserviceaccount.com \
    --memory=4Gi \
    --cpu=2 \
    --port=8000 \
    --set-env-vars="API_KEY=$(gcloud secrets versions access latest --secret=API_KEY)"

# Verify deployment
gcloud run services describe txtai --region=us-central1
```

### 3. Deploy persona-server Service

```bash
# Deploy service
gcloud run deploy persona-server \
    --source . \
    --region=us-central1 \
    --service-account=txtai-sa@aurite-dev.iam.gserviceaccount.com \
    --memory=2Gi \
    --cpu=1 \
    --port=3001

# Verify deployment
gcloud run services describe persona-server --region=us-central1
```

## Notes

- Using single service account (txtai-sa) for all services
- Cloud SQL and Redis instances are configured and ready
- Need to deploy txtai and persona-server services
- API_KEY secret needs to be created
- All build triggers are configured and working
