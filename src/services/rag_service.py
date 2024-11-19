import logging
from typing import Dict, Any, List, Optional
from .config_service import config_service
from .embeddings_service import embeddings_service
from ..models.messages import MessageType

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self._initialized = False
        self._embeddings_initialized = False

    async def initialize(self):
        """Initialize RAG service"""
        try:
            if not self._initialized:
                # Ensure embeddings service is initialized
                if not self._embeddings_initialized:
                    await embeddings_service.initialize()
                    self._embeddings_initialized = True
                    logger.info("Embeddings initialized for RAG service")

                self._initialized = True
                logger.info("RAG service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise

    async def generate(self, query: str, limit: int = 3) -> Dict[str, Any]:
        """Generate RAG response"""
        if not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            if not self._initialized:
                await self.initialize()

            # Get relevant context
            context = await self.search_context(query, limit)

            # Generate response using context
            response = {
                "query": query,
                "context": context,
                "response": "This is a test RAG response based on the provided context.",
            }

            logger.info(f"Generated RAG response: {response}")
            return response

        except Exception as e:
            logger.error(f"RAG generation failed: {str(e)}")
            raise

    async def search_context(
        self, query: str, limit: int = 3, min_score: float = 0.3
    ) -> List[Dict]:
        """Search for relevant context using embeddings"""
        if not self._initialized:
            await self.initialize()

        try:
            logger.info(f"\n=== Context Search ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")

            # Use embeddings service for search
            results = await embeddings_service.hybrid_search(query, limit)

            # Filter by minimum score
            results = [r for r in results if r.get("score", 0) >= min_score]
            logger.info(f"Found {len(results)} relevant documents")

            return results
        except Exception as e:
            logger.error(f"Context search failed: {str(e)}", exc_info=True)
            raise


# Global service instance
rag_service = RAGService()
