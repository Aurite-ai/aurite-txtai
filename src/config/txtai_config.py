from .settings import Settings
from typing import Dict, Any


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
    return {
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
