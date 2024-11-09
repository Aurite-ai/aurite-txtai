# GCP Configuration Documentation

## Project Details

- Project ID: `aurite-dev`
- Project Number: `422370317143`
- Region: `us-central1`

## Service Accounts

Currently configured service accounts:

- ✅ `txtai-sa@aurite-dev.iam.gserviceaccount.com`

  - Roles:
    - roles/run.invoker
    - roles/run.serviceAgent
    - roles/storage.objectCreator
    - roles/storage.objectViewer

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
  - Using service account: cloud-build-service-account@aurite-dev.iam.gserviceaccount.com
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

### 2. Update Build Trigger

Need to update via Console (https://console.cloud.google.com/cloud-build/triggers?project=aurite-dev):

- Change from tag to branch trigger
- Set branch pattern to ^main$
- Verify cloudbuild.yaml path
- Update substitutions:
  - \_API_KEY: $(gcloud secrets versions access latest --secret=API_KEY)
  - \_SA_KEY: $(gcloud secrets versions access latest --secret=txtai-sa-key)

### 3. Verify Service Account Permissions

Additional roles needed for txtai-sa:

```bash
# Grant Secret Manager access
gcloud projects add-iam-policy-binding aurite-dev \
    --member="serviceAccount:txtai-sa@aurite-dev.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Grant Cloud Run admin
gcloud projects add-iam-policy-binding aurite-dev \
    --member="serviceAccount:txtai-sa@aurite-dev.iam.gserviceaccount.com" \
    --role="roles/run.admin"

# Verify roles
gcloud projects get-iam-policy aurite-dev \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:serviceAccount:txtai-sa@aurite-dev.iam.gserviceaccount.com"
```

### 4. Initial Cloud Run Deployment

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

## Useful Commands

### Check Service Status

```bash
# Get service details
gcloud run services describe txtai --region=us-central1

# Get service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=txtai" --limit=10

# Get service URL
gcloud run services describe txtai --region=us-central1 --format 'value(status.url)'
```

### Manage Service Account Keys

```bash
# Create new key
gcloud iam service-accounts keys create key.json \
    --iam-account=txtai-sa@aurite-dev.iam.gserviceaccount.com

# List keys
gcloud iam service-accounts keys list \
    --iam-account=txtai-sa@aurite-dev.iam.gserviceaccount.com
```

## Notes

- Build failures need investigation after initial setup is complete
- Consider setting up monitoring and logging
- May need to adjust memory/CPU based on usage
- Remember to clean up old service account keys periodically
