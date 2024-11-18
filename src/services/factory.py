from typing import Tuple
from .embeddings_service import EmbeddingsService
from .query_service import QueryService
from ..config.settings import Settings


def create_services(settings: Settings) -> Tuple[EmbeddingsService, QueryService]:
    """Create and initialize services"""
    embeddings_service = EmbeddingsService(settings)
    embeddings = embeddings_service.create_index(settings.EMBEDDINGS_STORAGE_TYPE)
    query_service = QueryService(embeddings, settings)
    return embeddings_service, query_service
