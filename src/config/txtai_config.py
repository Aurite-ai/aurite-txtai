from .settings import Settings
from typing import Dict, Any

settings = Settings()


def create_llm_config(settings: Settings) -> dict:
    """Create LLM configuration"""
    return {
        "path": settings.LLM_MODELS[settings.LLM_PROVIDER],
        "api_key": (
            settings.ANTHROPIC_API_KEY
            if settings.LLM_PROVIDER == "anthropic"
            else settings.OPENAI_API_KEY
        ),
    }


def create_embeddings_config(settings: Settings) -> Dict[str, Any]:
    """Create embeddings configuration"""
    config = {
        "path": settings.EMBEDDINGS_MODEL,
        "content": True,
        "backend": "faiss",
        "hybrid": True,
        "normalize": True,
        "scoring": {
            "method": "bm25",
            "terms": True,
            "normalize": True,
            "weights": {"hybrid": 0.7, "terms": 0.3},
        },
        "batch": settings.EMBEDDINGS_BATCH_SIZE,
        "contentpath": settings.EMBEDDINGS_CONTENT_PATH,
        "database": True,
        "storetokens": True,
        "storeannoy": True,
    }

    # Add cloud configuration if using cloud storage
    if settings.EMBEDDINGS_STORAGE_TYPE == "cloud":
        config["cloud"] = {
            "provider": "gcs",
            "container": settings.GOOGLE_CLOUD_BUCKET,
            "prefix": settings.EMBEDDINGS_PREFIX,
        }
        config["contentpath"] = f"gcs://{settings.GOOGLE_CLOUD_BUCKET}"

    # Use memory storage if specified
    elif settings.EMBEDDINGS_STORAGE_TYPE == "memory":
        config["contentpath"] = ":memory:"

    return config


def create_storage_config(settings: Settings) -> dict:
    """Create storage-specific configuration"""
    if settings.EMBEDDINGS_STORAGE_TYPE == "memory":
        return {"contentpath": ":memory:"}
    elif settings.EMBEDDINGS_STORAGE_TYPE == "sqlite":
        return {"contentpath": settings.EMBEDDINGS_CONTENT_PATH, "batch": 1000}
    elif settings.EMBEDDINGS_STORAGE_TYPE == "cloud":
        return {
            "contentpath": settings.EMBEDDINGS_CONTENT_PATH,
            "cloud": {"provider": "gcs", "bucket": settings.GOOGLE_CLOUD_BUCKET},
            "batch": 500,
        }
    raise ValueError(f"Unknown storage type: {settings.EMBEDDINGS_STORAGE_TYPE}")
