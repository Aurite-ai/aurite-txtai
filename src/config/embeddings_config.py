from typing import Optional
from pydantic_settings import BaseSettings
from .settings import StorageType  # Import from settings


def get_embeddings_config(settings: BaseSettings) -> dict:
    """Get embeddings configuration for txtai

    Args:
        settings: Application settings

    Returns:
        Dict with txtai embeddings configuration
    """
    # Base configuration shared by all storage types
    config = {
        "path": settings.EMBEDDINGS_MODEL,
        "backend": "faiss",
        "hybrid": True,
        "normalize": True,
        "objects": True,
        "content": True,
        "scoring": {
            "method": "bm25",
            "terms": True,
            "normalize": True,
        },
    }

    # Storage-specific configurations
    if settings.EMBEDDINGS_STORAGE_TYPE == "memory":
        config.update(
            {
                "contentpath": ":memory:",
                "batch": 100,
            }
        )
    elif settings.EMBEDDINGS_STORAGE_TYPE == "sqlite":
        config.update(
            {
                "contentpath": settings.EMBEDDINGS_CONTENT_PATH,
                "batch": 1000,
            }
        )
    elif settings.EMBEDDINGS_STORAGE_TYPE == "cloud":
        if not settings.has_cloud_credentials:
            raise ValueError("Cloud storage selected but credentials not configured")

        config.update(
            {
                "batch": 500,
                "cloud": {
                    "provider": "gcs",
                    "container": settings.GOOGLE_CLOUD_BUCKET,
                    "prefix": settings.EMBEDDINGS_PREFIX,
                },
            }
        )
    else:
        raise ValueError(f"Invalid storage type: {settings.EMBEDDINGS_STORAGE_TYPE}")

    return config
