"""Service registry and initialization"""

import logging
from typing import Optional
from .config_service import config_service
from .txtai_service import txtai_service
from .embeddings_service import embeddings_service
from .rag_service import rag_service
from .llm_service import llm_service

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Central registry for all services"""

    def __init__(self):
        # Initialize references
        self._config_service = config_service
        self._txtai_service = txtai_service
        self._embeddings_service = embeddings_service
        self._rag_service = rag_service
        self._llm_service = llm_service
        self._initialized = False

    async def initialize(self):
        """Initialize all services in correct order"""
        if not self._initialized:
            logger.info("Initializing service registry...")

            try:
                # Initialize config first
                await self._config_service.initialize()
                logger.info("Config service initialized")

                # Initialize embeddings
                await self._embeddings_service.initialize()
                logger.info("Embeddings service initialized")

                # Initialize LLM (depends on config)
                await self._llm_service.initialize()
                logger.info("LLM service initialized")

                # Initialize RAG (depends on embeddings and LLM)
                await self._rag_service.initialize()
                logger.info("RAG service initialized")

                # Initialize txtai service last
                await self._txtai_service.initialize()
                logger.info("TxtAI service initialized")

                self._initialized = True
                logger.info("Service registry initialized")
            except Exception as e:
                logger.error(f"Service initialization failed: {e}")
                raise

    @property
    def config_service(self):
        return self._config_service

    @property
    def txtai_service(self):
        return self._txtai_service

    @property
    def embeddings_service(self):
        return self._embeddings_service

    @property
    def rag_service(self):
        return self._rag_service

    @property
    def llm_service(self):
        return self._llm_service


# Global registry instance
registry = ServiceRegistry()
