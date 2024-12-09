"""Service registry for accessing initialized services"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .base_service import BaseService
    from .embeddings_service import EmbeddingsService
    from .llm_service import LLMService
    from .rag_service import RAGService
    from .txtai_service import TxtAIService


class ServiceRegistry:
    """Registry for accessing initialized services"""

    _instance: ServiceRegistry | None = None
    _services: dict[str, BaseService] = {}

    def __new__(cls) -> ServiceRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def embeddings_service(self) -> EmbeddingsService | None:
        """Get the embeddings service.

        Returns:
            EmbeddingsService | None: The embeddings service if registered, None otherwise.
        """
        return self._services.get("embeddings")  # type: ignore

    @property
    def llm_service(self) -> LLMService | None:
        """Get the LLM service.

        Returns:
            LLMService | None: The LLM service if registered, None otherwise.
        """
        return self._services.get("llm")  # type: ignore

    @property
    def rag_service(self) -> RAGService | None:
        """Get the RAG service.

        Returns:
            RAGService | None: The RAG service if registered, None otherwise.
        """
        return self._services.get("rag")  # type: ignore

    @property
    def txtai_service(self) -> TxtAIService | None:
        """Get the txtai service.

        Returns:
            TxtAIService | None: The txtai service if registered, None otherwise.
        """
        return self._services.get("txtai")  # type: ignore

    def register_services(self, services: dict[str, BaseService]) -> None:
        """Register all services.

        Args:
            services: Dictionary mapping service names to service instances.
        """
        self._services = services


# Global instance
registry = ServiceRegistry()
