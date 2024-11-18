from .txtai_config import create_storage_config, create_embeddings_config
from .settings import Settings

settings = Settings()

__all__ = ["settings", "create_storage_config", "create_embeddings_config"]
