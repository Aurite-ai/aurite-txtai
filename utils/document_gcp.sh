#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check and set gcloud configuration
current_project=$(gcloud config get-value project 2>/dev/null)
current_region=$(gcloud config get-value compute/region 2>/dev/null)
current_zone=$(gcloud config get-value compute/zone 2>/dev/null)

[[ "$current_project" != "aurite-dev" ]] && gcloud config set project aurite-dev
[[ "$current_region" != "us-central1" ]] && gcloud config set compute/region us-central1
[[ "$current_zone" != "us-central1-a" ]] && gcloud config set compute/zone us-central1-a

# Export environment variables for setup_gcp.sh
export TXTAI_PROJECT_ID=aurite-dev
export TXTAI_REGION=us-central1
export TXTAI_ZONE=us-central1-a
export TXTAI_FIX_ISSUES=false
export TXTAI_NEEDS_GCR=false
export TXTAI_NEEDS_BUCKET=false
export TXTAI_NEEDS_SECRET=false
export TXTAI_NEEDS_TRIGGER=false

# Parse arguments
while getopts "f" opt; do
    case $opt in
        f) export TXTAI_FIX_ISSUES=true ;;
        *) echo "Usage: $0 [-f]" >&2; exit 1 ;;
    esac
done

# Initialize issue tracking
ISSUES=()
ISSUES_COUNT=0

# Function to track issues
track_issue() {
    ISSUES+=("✗ ${1}")
    ((ISSUES_COUNT++))
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "\n${BLUE}Prerequisites:${NC}"
    echo "Using project ID: ${TXTAI_PROJECT_ID}"

    # Check Container Registry
    echo -n "- Container Registry: "
    if gcloud container images list --repository=gcr.io/${TXTAI_PROJECT_ID} --filter="name:txtai-service" --format="get(name)" 2>/dev/null | grep -q "txtai-service"; then
        echo -e "${GREEN}✓${NC} (GCR repository exists)"
    else
        echo -e "${RED}✗${NC} (txtai-service repository not found in GCR)"
        track_issue "Container repository not found in GCR"
        export TXTAI_NEEDS_GCR=true
    fi

    # Check Required APIs
    local apis=("cloudbuild.googleapis.com" "run.googleapis.com" "secretmanager.googleapis.com" "storage.googleapis.com")
    for api in "${apis[@]}"; do
        echo -n "- $api: "
        if gcloud services list --filter=name:$api --format='value(STATE)' 2>/dev/null | grep -q ENABLED; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC} (not enabled)"
            track_issue "API $api not enabled"
        fi
    done
}

# Function to check Cloud Run service
check_cloud_run() {
    echo -e "\n${BLUE}Cloud Run Service:${NC}"
    if gcloud run services describe txtai-service --region=us-central1 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Service exists${NC}"

        # Check resource limits
        if ! gcloud run services describe txtai-service --region=us-central1 \
            --format="get(spec.template.spec.containers[0].resources)" 2>/dev/null | \
            grep -q "memory: 4Gi"; then
            echo -e "${RED}✗ Resource limits misconfigured${NC}"
            track_issue "Cloud Run service needs 4GB memory allocation"
        fi
    else
        echo -e "${RED}✗ Service not found${NC}"
        track_issue "Cloud Run service not deployed"
    fi
}

# Function to check components
check_components() {
    echo -e "\n${BLUE}Component Status:${NC}"

    # Check Secret Manager
    echo -n "- Secret Manager: "
    if ! gcloud secrets describe txtai-api-key >/dev/null 2>&1; then
        echo -e "${RED}✗ API key secret not found${NC}"
        track_issue "API key secret not configured"
        export TXTAI_NEEDS_SECRET=true
    else
        echo -e "${GREEN}✓${NC}"
    fi

    # Check Storage Bucket
    echo -n "- Storage Bucket: "
    if ! gsutil ls gs://aurite-txtai-dev >/dev/null 2>&1; then
        echo -e "${RED}✗ Bucket not found${NC}"
        track_issue "Storage bucket not configured"
        export TXTAI_NEEDS_BUCKET=true
    else
        echo -e "${GREEN}✓${NC}"
    fi

    # Check Service Account
    echo -n "- Service Account: "
    if ! gcloud iam service-accounts describe txtai-sa@aurite-dev.iam.gserviceaccount.com >/dev/null 2>&1; then
        echo -e "${RED}✗ Service account not found${NC}"
        track_issue "Service account not configured"
    else
        echo -e "${GREEN}✓${NC}"
    fi

    # Check Build Trigger
    echo -n "- Cloud Build Trigger: "
    local trigger_id=$(gcloud builds triggers list --region=us-central1 --filter="name~txtai-prod" --format="get(id)")
    if [ -z "$trigger_id" ]; then
        echo -e "${RED}✗ Build trigger not found${NC}"
        track_issue "Build trigger not configured"
        export TXTAI_NEEDS_TRIGGER=true
    else
        echo -e "${GREEN}✓${NC}"
    fi
}

# Function to check Cloud Build permissions
check_cloud_build_permissions() {
    echo -e "\n${BLUE}Cloud Build Permissions:${NC}"

    # Get Cloud Build service account
    local build_sa=$(gcloud projects get-value-from-metadata compute-service-account)
    echo -n "- Cloud Build Service Account: "
    if [ -n "$build_sa" ]; then
        echo -e "${GREEN}✓${NC} ($build_sa)"
    else
        echo -e "${RED}✗${NC} (not found)"
        track_issue "Cloud Build service account not found"
    fi

    # Check logging permissions
    echo -n "- Logging Permissions: "
    if gcloud projects get-iam-policy aurite-dev \
        --flatten="bindings[].members" \
        --format="table(bindings.role)" \
        --filter="bindings.members:$build_sa" | grep -q "roles/logging.logWriter"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC} (missing logging permissions)"
        track_issue "Cloud Build service account missing logging permissions"
        export TXTAI_NEEDS_BUILD_PERMS=true
    fi
}

# Add this function after check_cloud_build_permissions
check_secrets() {
    echo -e "\n${BLUE}Secret Manager Status:${NC}"

    # Check API Key Secret
    echo -n "- API Key Secret: "
    if ! gcloud secrets describe txtai-api-key >/dev/null 2>&1; then
        echo -e "${RED}✗ API key secret not found${NC}"
        track_issue "API key secret not configured"
        export TXTAI_NEEDS_API_KEY=true
    else
        echo -e "${GREEN}✓${NC}"
    fi

    # Check Service Account Key Secret
    echo -n "- Service Account Key Secret: "
    if ! gcloud secrets describe txtai-sa-key >/dev/null 2>&1; then
        echo -e "${RED}✗ Service account key secret not found${NC}"
        track_issue "Service account key secret not configured"
        export TXTAI_NEEDS_SA_KEY=true
    else
        echo -e "${GREEN}✓${NC}"
    fi

    # Check Build Trigger Configuration
    echo -n "- Build Trigger Secrets: "
    local trigger_id=$(gcloud builds triggers list --region=us-central1 --filter="name~txtai-prod" --format="get(id)")
    if [ -n "$trigger_id" ]; then
        local substitutions=$(gcloud builds triggers describe "$trigger_id" --region=us-central1 --format="get(substitutions)")
        if [[ "$substitutions" != *"_API_KEY"* ]] || [[ "$substitutions" != *"_SA_KEY"* ]]; then
            echo -e "${RED}✗ Missing secret substitutions${NC}"
            track_issue "Build trigger missing required secret substitutions"
            export TXTAI_NEEDS_TRIGGER_UPDATE=true
        else
            echo -e "${GREEN}✓${NC}"
        fi
    fi
}

# Main execution
check_prerequisites
check_cloud_build_permissions
check_secrets
check_components
check_cloud_run

# Print summary and handle fixes
echo -e "\n${BLUE}Summary:${NC}"
if [ $ISSUES_COUNT -gt 0 ]; then
    echo -e "${RED}Found $ISSUES_COUNT configuration issues:${NC}"
    for issue in "${ISSUES[@]}"; do
        echo -e "${RED}${issue}${NC}"
    done

    if [ "$TXTAI_FIX_ISSUES" = true ]; then
        echo -e "\n${YELLOW}Would you like to run the setup script to fix these issues? (y/n)${NC}"
        read -r REPLY
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "\n${YELLOW}Running setup script...${NC}"
            "${SCRIPT_DIR}/setup_gcp.sh"
        fi
    else
        echo -e "\n${YELLOW}Run with -f flag to fix these issues${NC}"
    fi
else
    echo -e "${GREEN}All components configured correctly${NC}"
fi