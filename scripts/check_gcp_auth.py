import os
import json
from google.cloud import storage
from google.auth import default
from pathlib import Path
import sys
import subprocess
import time

def create_service_account():
    """Create a service account using gcloud CLI"""
    print("\n=== Service Account Creation ===")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    sa_name = "txtai-service"
    sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
    bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET")
    
    try:
        # Create service account
        subprocess.run([
            "gcloud", "iam", "service-accounts", "create", sa_name,
            "--project", project_id,
            "--display-name", "txtai Service Account",
            "--description", "Service account for txtai embeddings storage"
        ], check=True, capture_output=True)
        print(f"✓ Created service account: {sa_email}")
        
        # Create and download key
        config_dir = Path("./config")
        config_dir.mkdir(exist_ok=True)
        key_path = config_dir / "service-account.json"
        
        subprocess.run([
            "gcloud", "iam", "service-accounts", "keys", "create",
            str(key_path),
            "--iam-account", sa_email,
            "--project", project_id
        ], check=True, capture_output=True)
        print(f"✓ Saved service account key to: {key_path}")

        # Create bucket if it doesn't exist
        try:
            subprocess.run([
                "gcloud", "storage", "buckets", "describe",
                f"gs://{bucket_name}",
                "--project", project_id
            ], check=True, capture_output=True)
            print(f"✓ Bucket exists: {bucket_name}")
        except subprocess.CalledProcessError:
            location = os.getenv("GCP_LOCATION", "us-central1")
            subprocess.run([
                "gcloud", "storage", "buckets", "create",
                f"gs://{bucket_name}",
                "--project", project_id,
                "--location", location,
                "--uniform-bucket-level-access"
            ], check=True, capture_output=True)
            print(f"✓ Created bucket: {bucket_name}")
        
        # Grant bucket-specific permissions
        roles = [
            "roles/storage.objectViewer",    # Read objects
            "roles/storage.objectCreator",   # Create objects
            "roles/storage.legacyBucketReader",  # List bucket contents
            "roles/storage.buckets.get"      # Get bucket metadata
        ]
        
        for role in roles:
            subprocess.run([
                "gcloud", "projects", "add-iam-policy-binding",
                project_id,
                "--member", f"serviceAccount:{sa_email}",
                "--role", role,
                "--condition", f"resource.name.startsWith('projects/_/buckets/{bucket_name}')",
                "--project", project_id
            ], check=True, capture_output=True)
            print(f"✓ Granted {role} to: {sa_email}")

        # Also grant storage.buckets.get at project level since it's needed for bucket operations
        subprocess.run([
            "gcloud", "projects", "add-iam-policy-binding",
            project_id,
            "--member", f"serviceAccount:{sa_email}",
            "--role", "roles/storage.objectViewer",
            "--project", project_id
        ], check=True, capture_output=True)
        
        print(f"✓ Granted project-level permissions to: {sa_email}")
        
        # Wait for permissions to propagate
        print("Waiting for permissions to propagate...")
        time.sleep(15)  # Increased wait time
        
        # Test bucket access with new credentials
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_path)
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Test write permissions
        blob = bucket.blob("test_permissions_delete_me")
        blob.upload_from_string("test")
        blob.delete()
        print(f"✓ Successfully verified bucket access and permissions")
        
        return str(key_path)
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create service account: {e.stderr.decode()}")
        return None
    except Exception as e:
        print(f"✗ Failed to create service account: {e}")
        return None

def check_gcloud_installed():
    """Check if gcloud CLI is installed and configured"""
    print("\n=== gcloud CLI Check ===")
    try:
        subprocess.run(["gcloud", "--version"], check=True, capture_output=True)
        print("✓ gcloud CLI is installed")
        
        # Check if user is authenticated
        result = subprocess.run(["gcloud", "auth", "list"], capture_output=True, text=True)
        if "No credentialed accounts." in result.stdout:
            print("✗ No gcloud authentication found. Please run: gcloud auth login")
            return False
        print("✓ gcloud CLI is authenticated")
        return True
    except subprocess.CalledProcessError:
        print("✗ gcloud CLI is not installed. Please install from: https://cloud.google.com/sdk/docs/install")
        return False
    except Exception as e:
        print(f"✗ Error checking gcloud CLI: {e}")
        return False

def check_env_vars():
    """Check required environment variables"""
    required_vars = {
        "GOOGLE_CLOUD_PROJECT": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "GOOGLE_CLOUD_BUCKET": os.getenv("GOOGLE_CLOUD_BUCKET"),
        "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    }
    
    print("\n=== Environment Variables ===")
    all_present = True
    for var, value in required_vars.items():
        status = "✓" if value else "✗"
        print(f"{status} {var}: {value or 'Not set'}")
        if not value:
            all_present = False
    
    return all_present

def check_credentials_file():
    """Check if credentials file exists and is readable"""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    print("\n=== Credentials File ===")
    if not creds_path:
        print("✗ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    path = Path(creds_path)
    if not path.exists():
        print(f"✗ Credentials file not found at: {creds_path}")
        return False
    
    if not path.is_file():
        print(f"✗ Path exists but is not a file: {creds_path}")
        return False
    
    try:
        if not os.access(creds_path, os.R_OK):
            print(f"✗ Credentials file not readable: {creds_path}")
            return False
        print(f"✓ Credentials file found and readable: {creds_path}")
        return True
    except Exception as e:
        print(f"✗ Error checking credentials file: {e}")
        return False

def check_gcp_auth():
    """Test GCP authentication"""
    print("\n=== GCP Authentication ===")
    try:
        credentials, project = default()
        print(f"✓ Successfully authenticated with GCP")
        print(f"✓ Using project: {project}")
        return True
    except Exception as e:
        print(f"✗ Failed to authenticate with GCP: {e}")
        return False

def check_bucket_access():
    """Test bucket access"""
    bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET")
    print("\n=== GCS Bucket Access ===")
    
    if not bucket_name:
        print("✗ GOOGLE_CLOUD_BUCKET not set")
        return False
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Test bucket existence
        if bucket.exists():
            print(f"✓ Successfully accessed bucket: {bucket_name}")
            
            # Test write permissions by attempting to create a test blob
            blob = bucket.blob("test_permissions_delete_me")
            blob.upload_from_string("test")
            blob.delete()
            print(f"✓ Successfully verified write permissions on bucket: {bucket_name}")
            return True
        else:
            print(f"✗ Bucket does not exist: {bucket_name}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to access bucket: {e}")
        return False

def main():
    print("GCP Authentication Diagnostic Tool")
    print("=================================")
    
    # First check if gcloud is installed and configured
    if not check_gcloud_installed():
        print("\n✗ Please install and configure gcloud CLI first")
        sys.exit(1)
    
    # Check environment variables
    check_env_vars()
    
    # Check credentials file
    if not check_credentials_file():
        print("\nNo valid service account credentials found.")
        response = input("Would you like to create a new service account? (y/n): ")
        if response.lower() == 'y':
            creds_path = create_service_account()
            if creds_path:
                print(f"\nPlease add this to your .env file:")
                print(f"GOOGLE_APPLICATION_CREDENTIALS={creds_path}")
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            sys.exit(1)
    
    # Run remaining checks
    checks = [
        check_gcp_auth(),
        check_bucket_access()
    ]
    
    print("\n=== Summary ===")
    if all(checks):
        print("✓ All checks passed! GCP authentication is properly configured.")
        sys.exit(0)
    else:
        print("✗ Some checks failed. Please review the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 