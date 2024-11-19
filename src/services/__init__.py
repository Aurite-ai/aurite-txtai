"""Service registry and initialization"""

import logging
from typing import Optional
from .base_service import BaseService
from .config_service import config_service
from .embeddings_service import embeddings_service
from .llm_service import llm_service
from .rag_service import rag_service
from .stream_service import stream_service
from .communication_service import communication_service
from .txtai_service import txtai_service

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Registry for all services"""

    def __init__(self):
        self.config_service = config_service
        self.embeddings_service = embeddings_service
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.stream_service = stream_service
        self.communication_service = communication_service
        self.txtai_service = txtai_service


# Global registry instance
registry = ServiceRegistry()

__all__ = [
    "BaseService",
    "config_service",
    "embeddings_service",
    "llm_service",
    "rag_service",
    "stream_service",
    "communication_service",
    "txtai_service",
    "registry",
]
