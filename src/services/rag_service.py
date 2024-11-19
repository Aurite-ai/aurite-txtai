import logging
from typing import List, Dict, Any
from .base_service import BaseService
from .embeddings_service import embeddings_service
from .config_service import config_service

logger = logging.getLogger(__name__)


class RAGService(BaseService):
    """Service for RAG operations"""

    def __init__(self):
        """Initialize RAG service"""
        super().__init__()
        self.embeddings_service = embeddings_service
        self.config_service = config_service

    async def initialize(self) -> None:
        """Initialize RAG service"""
        if not self.initialized:
            try:
                # Get settings from config service
                self.settings = self.config_service.settings

                # Mark as initialized
                self._initialized = True
                logger.info("RAG service initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize RAG service: {e}")
                raise

    async def get_context(self, query: str, limit: int = 3) -> str:
        """Get relevant context for a query"""
        self._check_initialized()
        try:
            logger.info(f"Getting context for query: {query}")

            # Search for relevant documents
            results = await self.embeddings_service.search(query, limit=limit)
            logger.info(f"Raw search results: {results}")

            # Filter and format results
            filtered_results = [r for r in results if r["score"] > 0.3]
            logger.info(f"Filtered results: {filtered_results}")
            logger.info(f"Found {len(filtered_results)} relevant documents")

            # Combine context
            context = " ".join([r["text"] for r in filtered_results])
            return context

        except Exception as e:
            logger.error(f"Failed to get context: {str(e)}")
            raise


# Global service instance
rag_service = RAGService()
