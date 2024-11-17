from pathlib import Path
import subprocess
import os

def check_or_create_service_account():
    """Check existing service account or create if needed"""
    print("\n=== Service Account Setup ===")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    sa_name = "txtai-service"
    sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
    bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET")

    # Check if service account exists
    try:
        subprocess.run([
            "gcloud", "iam", "service-accounts", "describe",
            sa_email,
            "--project", project_id
        ], check=True, capture_output=True)
        print(f"✓ Service account exists: {sa_email}")
    except subprocess.CalledProcessError:
        # Create if it doesn't exist
        try:
            subprocess.run([
                "gcloud", "iam", "service-accounts", "create", sa_name,
                "--project", project_id,
                "--display-name", "txtai Service Account",
                "--description", "Service account for txtai embeddings storage"
            ], check=True, capture_output=True)
            print(f"✓ Created service account: {sa_email}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create service account: {e.stderr.decode()}")
            return False

    # Check/create key file
    config_dir = Path("./config")
    config_dir.mkdir(exist_ok=True)
    key_path = config_dir / "service-account.json"

    if not key_path.exists():
        try:
            subprocess.run([
                "gcloud", "iam", "service-accounts", "keys", "create",
                str(key_path),
                "--iam-account", sa_email,
                "--project", project_id
            ], check=True, capture_output=True)
            print(f"✓ Created new service account key: {key_path}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create service account key: {e.stderr.decode()}")
            return False
    else:
        print(f"✓ Service account key exists: {key_path}")

    # Check/create bucket
    try:
        subprocess.run([
            "gcloud", "storage", "buckets", "describe",
            f"gs://{bucket_name}",
            "--project", project_id
        ], check=True, capture_output=True)
        print(f"✓ Bucket exists: {bucket_name}")
    except subprocess.CalledProcessError:
        try:
            location = os.getenv("GCP_LOCATION", "us-central1")
            subprocess.run([
                "gcloud", "storage", "buckets", "create",
                f"gs://{bucket_name}",
                "--project", project_id,
                "--location", location,
                "--uniform-bucket-level-access"
            ], check=True, capture_output=True)
            print(f"✓ Created bucket: {bucket_name}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create/verify bucket: {e.stderr.decode()}")
            return False

    return True

if __name__ == "__main__":
    if not check_or_create_service_account():
        exit(1)
    print("\n✓ GCP authentication setup complete")