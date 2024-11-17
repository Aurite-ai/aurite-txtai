from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field

StorageType = Literal["memory", "sqlite", "cloud"]
QueryType = Literal["sql", "semantic", "hybrid"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Embeddings Settings - Core settings from notebooks
    EMBEDDINGS_MODEL: str = "sentence-transformers/nli-mpnet-base-v2"
    EMBEDDINGS_STORAGE_TYPE: StorageType = Field(
        default="memory", description="Storage backend type (memory, sqlite, cloud)"
    )
    EMBEDDINGS_CONTENT_PATH: str = "txtai/content.db"
    EMBEDDINGS_PREFIX: str = "txtai"

    # Query Settings
    DEFAULT_QUERY_TYPE: QueryType = Field(
        default="hybrid", description="Default search type (sql, semantic, hybrid)"
    )

    # Cloud Settings - Only needed for cloud storage
    GOOGLE_CLOUD_PROJECT: str = "aurite-dev"
    GOOGLE_CLOUD_BUCKET: str = "aurite-txtai-dev"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # API Settings - Required for service
    API_KEY: str = ""

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="allow")

    @property
    def has_cloud_credentials(self) -> bool:
        """Check if cloud credentials are configured"""
        return bool(self.GOOGLE_APPLICATION_CREDENTIALS)
