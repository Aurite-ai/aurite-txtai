from typing import Optional
from google.cloud import storage
from google.oauth2 import service_account
from google.auth import default
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    # GCP Settings
    GOOGLE_CLOUD_PROJECT: str = "aurite-dev"
    GOOGLE_CLOUD_BUCKET: str = "aurite-txtai-dev"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Embeddings Settings
    EMBEDDINGS_MODEL: str = "sentence-transformers/nli-mpnet-base-v2"
    EMBEDDINGS_PREFIX: str = "txtai"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

class ConfigService:
    """Service for managing application configuration and cloud resources"""
    
    def __init__(self):
        self.settings = Settings()
        self._storage_client = None
        
    @property
    def storage_client(self) -> storage.Client:
        """Get or create Google Cloud Storage client"""
        if not self._storage_client:
            try:
                # First try application default credentials
                credentials, project = default()
                self._storage_client = storage.Client(
                    project=self.settings.GOOGLE_CLOUD_PROJECT,
                    credentials=credentials
                )
            except Exception as e:
                print(f"Warning: Failed to use application default credentials: {str(e)}")
                # Fallback to explicit credentials file if specified
                if self.settings.GOOGLE_APPLICATION_CREDENTIALS:
                    try:
                        credentials = service_account.Credentials.from_service_account_file(
                            self.settings.GOOGLE_APPLICATION_CREDENTIALS
                        )
                        self._storage_client = storage.Client(
                            project=self.settings.GOOGLE_CLOUD_PROJECT,
                            credentials=credentials
                        )
                    except Exception as e:
                        print(f"Warning: Failed to use service account credentials: {str(e)}")
                        self._storage_client = self._get_anonymous_client()
                else:
                    self._storage_client = self._get_anonymous_client()
                    
        return self._storage_client
    
    def _get_anonymous_client(self) -> storage.Client:
        """Get anonymous storage client for testing"""
        print("Warning: Using anonymous storage client - limited functionality available")
        return storage.Client.create_anonymous_client()
    
    @property
    def embeddings_config(self) -> dict:
        """Get embeddings configuration"""
        return {
            "path": self.settings.EMBEDDINGS_MODEL,
            "cloud": {
                "provider": "gcs",
                "container": self.settings.GOOGLE_CLOUD_BUCKET,
                "prefix": self.settings.EMBEDDINGS_PREFIX
            }
        }
    
    def init_storage(self):
        """Initialize storage bucket if it doesn't exist"""
        try:
            if not self.storage_client.lookup_bucket(self.settings.GOOGLE_CLOUD_BUCKET):
                bucket = self.storage_client.create_bucket(self.settings.GOOGLE_CLOUD_BUCKET)
                print(f"Created bucket: {bucket.name}")
            return True
        except Exception as e:
            print(f"Warning: Failed to initialize storage: {str(e)}")
            return False

# Global config service instance
config_service = ConfigService()