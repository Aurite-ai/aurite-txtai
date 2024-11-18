from .settings import Settings


def create_embeddings_config(settings: Settings) -> dict:
    """Create txtai embeddings configuration"""
    base_config = {
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
    }

    # Add storage configuration
    if settings.EMBEDDINGS_STORAGE_TYPE == "memory":
        base_config["contentpath"] = ":memory:"
    else:
        base_config["contentpath"] = settings.EMBEDDINGS_CONTENT_PATH
        base_config["batch"] = 1000

    return base_config


def create_storage_config(settings: Settings) -> dict:
    """Create storage-specific configuration"""
    if settings.EMBEDDINGS_STORAGE_TYPE == "memory":
        return {"contentpath": ":memory:"}
    elif settings.EMBEDDINGS_STORAGE_TYPE == "sqlite":
        return {"contentpath": settings.STORAGE_PATH, "batch": 1000}
    elif settings.EMBEDDINGS_STORAGE_TYPE == "cloud":
        return {
            "contentpath": settings.STORAGE_PATH,
            "cloud": {"provider": "gcs", "bucket": settings.GOOGLE_CLOUD_BUCKET},
            "batch": 500,
        }
    raise ValueError(f"Unknown storage type: {settings.EMBEDDINGS_STORAGE_TYPE}")
