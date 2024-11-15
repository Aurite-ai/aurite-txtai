from typing import Optional
from pydantic_settings import BaseSettings

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
    """Service for managing application configuration"""
    
    def __init__(self):
        self.settings = Settings()
    
    @property
    def embeddings_config(self) -> dict:
        """Get embeddings configuration for txtai"""
        return {
            "path": self.settings.EMBEDDINGS_MODEL,
            "content": True,
            "hybrid": True,
            "scoring": {
                "method": "bm25",
                "terms": True,
                "normalize": True
            },
            "batch": 32,
            "backend": "faiss",
            "normalize": True,
            "cloud": {
                "provider": "gcs",
                "container": self.settings.GOOGLE_CLOUD_BUCKET,
                "prefix": self.settings.EMBEDDINGS_PREFIX
            }
        }

# Global config service instance
config_service = ConfigService()