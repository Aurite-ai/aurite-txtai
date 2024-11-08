#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Error handling
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo -e "${RED}Error: Command \"${last_command}\" failed with exit code $?${NC}"' ERR

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check configuration
check_configuration() {
    echo -e "\n${BLUE}Checking configuration after fixes...${NC}"
    # Run document_gcp.sh without fix flag to avoid circular execution
    TXTAI_FIX_ISSUES=false "${SCRIPT_DIR}/document_gcp.sh"
}

# Function to run cloud build dry run
run_cloud_build_dry_run() {
    echo -e "\n${BLUE}Running Cloud Build validation...${NC}"
    echo "This will validate the cloudbuild.yaml configuration"
    local log_file="${SCRIPT_DIR}/build_log.txt"

    if [ -f "${SCRIPT_DIR}/../cloudbuild.yaml" ]; then
        echo "Validating build configuration..."

        # Show what would be deployed
        {
            echo "Cloud Build Validation Log"
            echo "=========================="
            echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
            echo -e "\nDeployment Configuration:"
            echo "------------------------"
            echo "Service: txtai-service"
            echo "Region: us-central1"
            echo "Memory: 4Gi"
            echo "CPU: 2"
            echo "Image: gcr.io/${TXTAI_PROJECT_ID}/txtai-service"
            echo "Service Account: txtai-sa@${TXTAI_PROJECT_ID}.iam.gserviceaccount.com"
            echo -e "\nBuild Output:"
            echo "------------"
        } > "$log_file"

        # Run validation and append output to log file
        if gcloud builds submit --no-source \
            --config="${SCRIPT_DIR}/../cloudbuild.yaml" \
            --substitutions=_API_KEY="test-api-key" >> "$log_file" 2>&1; then

            echo -e "${GREEN}✓ Cloud Build configuration validated${NC}"
            echo -e "Build log saved to: ${YELLOW}${log_file}${NC}"
        else
            echo -e "${RED}✗ Cloud Build validation failed${NC}"
            echo -e "See detailed error log in: ${YELLOW}${log_file}${NC}"
            return 1
        fi
    else
        echo -e "${RED}Error: cloudbuild.yaml not found at ${SCRIPT_DIR}/../cloudbuild.yaml${NC}"
        return 1
    fi
}

# Function to setup container registry
setup_container_registry() {
    local project_id=$1
    echo -e "\n${BLUE}Setting up Container Registry...${NC}"

    # Enable Container Registry API
    echo "Enabling Container Registry API..."
    if ! gcloud services list --filter=name:containerregistry.googleapis.com --format='value(STATE)' | grep -q ENABLED; then
        gcloud services enable containerregistry.googleapis.com
        echo -e "${GREEN}✓ Container Registry API enabled${NC}"
    else
        echo -e "${GREEN}✓ Container Registry API already enabled${NC}"
    fi

    # Configure docker authentication
    echo "Configuring docker authentication..."
    gcloud auth configure-docker gcr.io -q
    echo -e "${GREEN}✓ Docker authentication configured${NC}"

    # Create initial repository with minimal image
    echo "Creating initial repository..."
    if ! gcloud container images list --repository=gcr.io/${project_id} --filter="name:txtai-service" --format="get(name)" 2>/dev/null | grep -q "txtai-service"; then
        echo "Pulling alpine image for initialization..."
        docker pull alpine:latest

        echo "Tagging image for GCR..."
        docker tag alpine:latest "gcr.io/${project_id}/txtai-service:init"

        echo "Pushing image to GCR..."
        docker push "gcr.io/${project_id}/txtai-service:init"

        echo "Cleaning up local images..."
        docker rmi "gcr.io/${project_id}/txtai-service:init"
        docker rmi alpine:latest

        echo -e "${GREEN}✓ GCR repository created successfully${NC}"
    else
        echo -e "${YELLOW}! GCR repository already exists${NC}"
    fi
}

# Function to setup storage bucket
setup_storage_bucket() {
    local project_id=$1
    echo -e "\n${BLUE}Setting up Storage Bucket...${NC}"

    if ! gsutil ls gs://aurite-txtai-dev >/dev/null 2>&1; then
        echo "Creating storage bucket..."
        gsutil mb -p "${project_id}" -l us-central1 "gs://aurite-txtai-dev"
        echo "Setting bucket permissions..."
        gsutil iam ch "serviceAccount:txtai-sa@${project_id}.iam.gserviceaccount.com:objectAdmin" "gs://aurite-txtai-dev"
        echo -e "${GREEN}✓ Storage bucket created and configured${NC}"
    else
        echo -e "${YELLOW}! Storage bucket already exists${NC}"
    fi
}

# Function to setup API key
setup_api_key() {
    local project_id=$1
    echo -e "\n${BLUE}Setting up API Key Secret...${NC}"

    if ! gcloud secrets describe txtai-api-key >/dev/null 2>&1; then
        echo "Creating API key secret..."
        read -p "Enter API Key value: " api_key
        if [ -z "$api_key" ]; then
            echo -e "${RED}Error: API key cannot be empty${NC}"
            return 1
        fi
        echo -n "$api_key" | gcloud secrets create txtai-api-key --data-file=-
        echo -e "${GREEN}✓ API key secret created${NC}"
    else
        echo -e "${YELLOW}! API key secret already exists${NC}"
    fi
}

# Function to setup build trigger
setup_build_trigger() {
    local project_id=$1
    local trigger_id=$2
    echo -e "\n${BLUE}Setting up Build Trigger...${NC}"

    if [ -n "$trigger_id" ]; then
        echo "Updating build trigger..."
        gcloud builds triggers update "$trigger_id" \
            --region=us-central1 \
            --substitutions=_API_KEY='$(gcloud secrets versions access latest --secret=txtai-api-key)'
        echo -e "${GREEN}✓ Build trigger updated${NC}"
    else
        echo -e "${YELLOW}! No trigger ID provided${NC}"
    fi
}

# Add this function after the existing setup functions
setup_cloud_build_permissions() {
    local project_id=$1
    echo -e "\n${BLUE}Setting up Cloud Build Permissions...${NC}"

    # Get Cloud Build service account
    local build_sa=$(gcloud projects get-value-from-metadata compute-service-account)
    if [ -z "$build_sa" ]; then
        echo -e "${RED}Error: Could not determine Cloud Build service account${NC}"
        return 1
    fi

    echo "Granting logging permissions to $build_sa..."
    if ! gcloud projects add-iam-policy-binding "$project_id" \
        --member="serviceAccount:$build_sa" \
        --role="roles/logging.logWriter" > /dev/null 2>&1; then
        echo -e "${RED}Error: Failed to grant logging permissions${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Logging permissions granted${NC}"

    # Verify permissions
    if gcloud projects get-iam-policy "$project_id" \
        --flatten="bindings[].members" \
        --format="table(bindings.role)" \
        --filter="bindings.members:$build_sa" | grep -q "roles/logging.logWriter"; then
        echo -e "${GREEN}✓ Permissions verified${NC}"
    else
        echo -e "${RED}Error: Permission verification failed${NC}"
        return 1
    fi
}

# Main execution
if [[ -z "${TXTAI_PROJECT_ID}" ]]; then
    echo -e "${RED}Error: TXTAI_PROJECT_ID not set${NC}"
    exit 1
fi

if [[ -z "${TXTAI_FIX_ISSUES}" ]]; then
    echo -e "${RED}Error: TXTAI_FIX_ISSUES not set${NC}"
    exit 1
fi

if [[ "${TXTAI_FIX_ISSUES}" != "true" ]]; then
    echo "Fix issues not enabled, exiting"
    exit 0
fi

echo -e "${BLUE}Starting GCP setup with project: ${TXTAI_PROJECT_ID}${NC}"

# Execute fixes based on needs
FIXES_APPLIED=false

if [[ "${TXTAI_NEEDS_GCR}" == "true" ]]; then
    setup_container_registry "${TXTAI_PROJECT_ID}"
    FIXES_APPLIED=true
fi

if [[ "${TXTAI_NEEDS_BUCKET}" == "true" ]]; then
    setup_storage_bucket "${TXTAI_PROJECT_ID}"
    FIXES_APPLIED=true
fi

if [[ "${TXTAI_NEEDS_SECRET}" == "true" ]]; then
    setup_api_key "${TXTAI_PROJECT_ID}"
    FIXES_APPLIED=true
fi

if [[ "${TXTAI_NEEDS_TRIGGER}" == "true" ]]; then
    trigger_id=$(gcloud builds triggers list --region=us-central1 --filter="name~txtai-prod" --format="get(id)")
    if [[ -n "$trigger_id" ]]; then
        setup_build_trigger "${TXTAI_PROJECT_ID}" "$trigger_id"
        FIXES_APPLIED=true
    fi
fi

if [[ "${TXTAI_NEEDS_BUILD_PERMS}" == "true" ]]; then
    setup_cloud_build_permissions "${TXTAI_PROJECT_ID}"
    FIXES_APPLIED=true
fi

if [ "$FIXES_APPLIED" = true ]; then
    echo -e "\n${GREEN}Fixes applied successfully${NC}"
    # Check configuration after fixes
    check_configuration
else
    echo -e "\n${GREEN}No fixes needed${NC}"
    # Offer to run cloud build dry run
    echo -e "\n${YELLOW}Would you like to run a Cloud Build dry run to validate deployment? (y/n)${NC}"
    read -r REPLY
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_cloud_build_dry_run
    fi
fi

echo -e "\n${GREEN}GCP setup complete${NC}"