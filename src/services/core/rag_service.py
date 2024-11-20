import logging
from typing import List, Dict, Any, Optional
from ..base_service import BaseService
from .embeddings_service import EmbeddingsService
from .llm_service import LLMService
from src.config import Settings

logger = logging.getLogger(__name__)


class RAGService(BaseService):
    """Service for RAG operations"""

    def __init__(self):
        """Initialize RAG service"""
        super().__init__()
        self.settings: Optional[Settings] = None
        self.embeddings_service: Optional[EmbeddingsService] = None
        self.llm_service: Optional[LLMService] = None

    async def initialize(
        self,
        settings: Settings = None,
        embeddings_service: Optional[EmbeddingsService] = None,
        llm_service: Optional[LLMService] = None,
    ) -> None:
        """Initialize RAG service with dependencies"""
        if not self.initialized:
            try:
                # Get or create settings
                self.settings = settings or Settings()

                # Set service dependencies
                self.embeddings_service = embeddings_service
                self.llm_service = llm_service

                # Verify dependencies are initialized
                if not (self.embeddings_service and self.embeddings_service.initialized):
                    raise ValueError("Embeddings service must be initialized")
                if not (self.llm_service and self.llm_service.initialized):
                    raise ValueError("LLM service must be initialized")

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
            # Get context with proper parameters
            context = await self.search_context(query, limit=3)  # Using default limit
            if not context:
                return "No relevant context found to answer the question."

            # Format context for LLM with proper structure
            context_text = "\n\nRelevant context:\n" + "\n---\n".join(
                f"{r['text']}"
                + (
                    f" (Source: {r['metadata'].get('source', 'Unknown')})"
                    if r.get('metadata')
                    else ""
                )
                for r in context
            )

            # Generate response using LLM with context and system prompt
            system_prompt = self.settings.SYSTEM_PROMPTS.get(
                "rag", "You are a helpful AI assistant."
            )
            prompt = (
                f"Based on the following context, answer the question. "
                f"If the context doesn't contain relevant information, say so.\n\n"
                f"Question: {query}\n\n{context_text}"
            )

            response = await self.llm_service.generate_with_context(prompt, system=system_prompt)

            logger.info(f"Generated RAG response for query: {query[:50]}...")
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
            # Use hybrid search as specified in SERVICE.md
            results = await self.embeddings_service.hybrid_search(query, limit=limit)

            # Filter and format results
            filtered_results = [
                {
                    "text": r["text"],
                    "score": r["score"],
                    "metadata": r.get("metadata", {}),
                    "id": r.get("id", ""),
                }
                for r in results
                if r["score"] > min_score
            ]

            logger.info(f"Found {len(filtered_results)} relevant documents above score threshold")
            return filtered_results

        except Exception as e:
            logger.error(f"Context search failed: {e}")
            raise


# Global service instance
rag_service = RAGService()
