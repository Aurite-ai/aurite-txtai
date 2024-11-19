import logging
from typing import List, Dict, Any
from .base_service import BaseService
from .embeddings_service import embeddings_service
from .config_service import config_service
from .llm_service import llm_service

logger = logging.getLogger(__name__)


class RAGService(BaseService):
    """Service for RAG operations"""

    def __init__(self):
        """Initialize RAG service"""
        super().__init__()
        self.embeddings_service = embeddings_service
        self.config_service = config_service
        self.llm_service = llm_service

    async def initialize(self) -> None:
        """Initialize RAG service"""
        if not self.initialized:
            try:
                # Get settings from config service
                self.settings = self.config_service.settings
                self._initialized = True
                logger.info("RAG service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize RAG service: {e}")
                raise

    async def generate(self, query: str) -> str:
        """Generate response using RAG"""
        self._check_initialized()

        if not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Get context
            context = await self.get_context(query)
            if not context:
                return "No relevant context found to answer the question."

            # Generate response using LLM with context
            response = await self.llm_service.generate_with_context(query, context)
            return response

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    async def search_context(
        self, query: str, limit: int = 3, min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search for relevant context"""
        self._check_initialized()
        try:
            # Search for documents
            results = await self.embeddings_service.search(query, limit=limit)

            # Filter by minimum score
            filtered_results = [r for r in results if r["score"] > min_score]
            logger.info(f"Found {len(filtered_results)} relevant documents above score threshold")

            return filtered_results

        except Exception as e:
            logger.error(f"Context search failed: {e}")
            raise

    async def get_context(self, query: str, limit: int = 3) -> str:
        """Get context for query"""
        self._check_initialized()
        try:
            # Search for relevant documents
            results = await self.search_context(query, limit=limit)

            # Combine context from relevant documents
            context = " ".join([r["text"] for r in results])
            logger.info(f"Generated context of length: {len(context)}")

            return context

        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            raise


# Global service instance
rag_service = RAGService()
