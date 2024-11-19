import logging
from typing import Dict, Any, List, Optional
from .config_service import config_service
from .embeddings_service import embeddings_service
from ..models.messages import MessageType
from .base_service import BaseService
from .llm_service import llm_service

logger = logging.getLogger(__name__)


class RAGService(BaseService):
    """Service to handle RAG operations"""

    async def initialize(self):
        """Initialize RAG service"""
        if not self.initialized:
            try:
                # Ensure embeddings service is initialized
                await embeddings_service.initialize()
                # Ensure LLM service is initialized
                await llm_service.initialize()

                self._initialized = True
                logger.info("RAG service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize RAG service: {e}")
                raise

    async def generate(self, query: str, limit: int = 3) -> Dict[str, Any]:
        """Generate RAG response"""
        self._check_initialized()
        if not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Get relevant context
            context = await self.search_context(query, limit)
            context_text = "\n".join(doc["text"] for doc in context) if context else ""

            # Generate response
            response = (
                llm_service.generate_with_context(query, context_text)
                if context
                else "No relevant context found."
            )

            return {"query": query, "context": context, "response": response}
        except Exception as e:
            logger.error(f"RAG generation failed: {str(e)}")
            raise

    async def search_context(
        self, query: str, limit: int = 3, min_score: float = 0.3
    ) -> List[Dict]:
        """Search for relevant context using embeddings"""
        self._check_initialized()

        try:
            logger.info(f"\n=== Context Search ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")
            logger.info(f"Min score: {min_score}")

            # Use embeddings service for search
            results = await embeddings_service.hybrid_search(query, limit)
            logger.info(f"Raw search results: {results}")

            # Filter by minimum score
            results = [r for r in results if r.get("score", 0) >= min_score]
            logger.info(f"Filtered results: {results}")
            logger.info(f"Found {len(results)} relevant documents")

            return results
        except Exception as e:
            logger.error(f"Context search failed: {str(e)}", exc_info=True)
            raise


# Global service instance
rag_service = RAGService()
