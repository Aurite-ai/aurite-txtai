from typing import Optional
from pydantic_settings import BaseSettings
from txtai.api import API
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
    API_KEY: str

    # Embeddings Settings
    EMBEDDINGS_MODEL: str = "sentence-transformers/nli-mpnet-base-v2"
    EMBEDDINGS_PREFIX: str = "txtai"
    EMBEDDINGS_BATCH_SIZE: int = 32
    EMBEDDINGS_CONTENT_PATH: str = "txtai/content.db"
    EMBEDDINGS_STORAGE_TYPE: str = "cloud"  # Options: memory, sqlite, cloud

    # LLM Settings
    LLM_MODEL: str = "TheBloke/Mistral-7B-OpenOrca-AWQ"
    LLM_DTYPE: str = "torch.bfloat16"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "anthropic"  # or "openai"

    class Config:
        env_file = ".env"
        case_sensitive = True

class ConfigService:
    """Service for managing application configuration"""

    def __init__(self):
        self.settings = Settings()
        self._api_config = None
        self.initialize_api()

    def initialize_api(self):
        """Initialize the txtai API configuration"""
        self._api_config = API({
            "embeddings": {
                "path": self.settings.EMBEDDINGS_MODEL,
                "content": True,
                "backend": "faiss"
            },
            "token": self.settings.API_KEY  # Token goes in config dict
        })

    @property
    def embeddings_config(self) -> dict:
        """Get embeddings configuration for txtai"""
        base_config = {
            "path": self.settings.EMBEDDINGS_MODEL,
            "content": True,
            "backend": "faiss",
            "hybrid": True,
            "scoring": {
                "method": "bm25",
                "terms": True,
                "normalize": True
            },
            "batch": self.settings.EMBEDDINGS_BATCH_SIZE,
            "normalize": True,
        }

        # Add storage-specific config based on type
        if self.settings.EMBEDDINGS_STORAGE_TYPE == "cloud":
            base_config.update({
                "cloud": {
                    "provider": "gcs",
                    "container": self.settings.GOOGLE_CLOUD_BUCKET,
                    "prefix": self.settings.EMBEDDINGS_PREFIX
                }
            })
        elif self.settings.EMBEDDINGS_STORAGE_TYPE == "sqlite":
            base_config["contentpath"] = self.settings.EMBEDDINGS_CONTENT_PATH

        return base_config

    @property
    def api_config(self) -> dict:
        """Get API configuration for txtai"""
        return self._api_config

# Global config service instance
config_service = ConfigService()