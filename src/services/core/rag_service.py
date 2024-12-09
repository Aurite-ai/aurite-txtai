from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypedDict

from src.services.base_service import BaseService


if TYPE_CHECKING:
    from src.config import Settings
    from src.services.core.embeddings_service import EmbeddingsService
    from src.services.core.llm_service import LLMService


logger = logging.getLogger(__name__)


class RAGResult(TypedDict):
    """Type definition for RAG result"""

    question: str
    context: str
    answer: str


class RAGService(BaseService):
    """Service for Retrieval Augmented Generation operations"""

    def __init__(self) -> None:
        """Initialize RAG service"""
        super().__init__()
        self.embeddings_service: EmbeddingsService | None = None
        self.llm_service: LLMService | None = None

    async def initialize(
        self,
        settings: Settings,
        embeddings_service: EmbeddingsService | None = None,
        llm_service: LLMService | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize RAG service with configuration

        Args:
            settings: Application settings
            embeddings_service: Optional pre-initialized embeddings service
            llm_service: Optional pre-initialized LLM service
            **kwargs: Additional configuration options

        Raises:
            Exception: If initialization fails
        """
        try:
            await super().initialize(settings, **kwargs)

            if not self._initialized:
                # Set required services
                self.embeddings_service = embeddings_service
                self.llm_service = llm_service

                self._initialized = True
                logger.info("RAG service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e!s}")
            raise

    async def answer(
        self,
        question: str,
        limit: int = 3,
        min_score: float = 0.0,
        temperature: float = 0.7,
    ) -> RAGResult:
        """Answer a question using RAG

        Args:
            question: Question to answer
            limit: Maximum number of context documents to retrieve
            min_score: Minimum relevance score for context documents
            temperature: LLM temperature for answer generation

        Returns:
            RAGResult: Question, context used, and generated answer
        """
        try:
            self._check_initialized()
            if not self.embeddings_service or not self.llm_service:
                raise RuntimeError("Required services not initialized")

            # Search for relevant context
            results = await self.embeddings_service.hybrid_search(
                query=question,
                limit=limit,
                min_score=min_score,
            )

            # Format context from results
            context = (
                "\n\n".join(f"Document {i+1}:\n{r['text']}" for i, r in enumerate(results))
                if results
                else "No relevant context found."
            )

            # Generate answer using context
            system_prompt = self.settings.SYSTEM_PROMPTS.get(
                "rag", "You are a helpful AI assistant."
            )
            prompt = (
                f"Answer this question using ONLY the context below:\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {question}\n\n"
                f"Answer:"
            )

            answer = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
            )

            return {
                "question": question,
                "context": context,
                "answer": answer,
            }

        except Exception as e:
            logger.error(f"RAG answer generation failed: {e!s}")
            return {
                "question": question,
                "context": "Error retrieving context",
                "answer": "Failed to generate answer due to an error",
            }


# Global service instance
rag_service = RAGService()
