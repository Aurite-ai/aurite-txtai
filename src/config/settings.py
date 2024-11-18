from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field

StorageType = Literal["memory", "sqlite", "cloud"]
QueryType = Literal["sql", "semantic", "hybrid"]


class Settings(BaseSettings):
    """Application runtime settings from environment"""

    # Embeddings Core Settings
    EMBEDDINGS_MODEL: str = "sentence-transformers/nli-mpnet-base-v2"
    EMBEDDINGS_STORAGE_TYPE: StorageType = Field(
        default="memory", description="Storage backend type (memory, sqlite, cloud)"
    )

    # Storage Settings
    STORAGE_PATH: str = "txtai/content.db"
    STORAGE_PREFIX: str = "txtai"
    EMBEDDINGS_CONTENT_PATH: str = "txtai/content.db"
    EMBEDDINGS_PREFIX: str = "txtai"
    EMBEDDINGS_BATCH_SIZE: int = Field(
        default=32, description="Batch size for document indexing"
    )

    # Search Settings
    DEFAULT_QUERY_TYPE: QueryType = Field(
        default="hybrid", description="Default search type (sql, semantic, hybrid)"
    )

    # Cloud Provider Settings
    GOOGLE_CLOUD_PROJECT: str = "aurite-dev"
    GOOGLE_CLOUD_BUCKET: str = "aurite-txtai-dev"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # API Settings
    API_KEY: str
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Python Settings
    PYTHONPATH: Optional[str] = None

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    @property
    def has_cloud_credentials(self) -> bool:
        """Check if cloud credentials are configured"""
        return bool(self.GOOGLE_APPLICATION_CREDENTIALS)
