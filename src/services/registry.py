"""Service registry for accessing initialized services"""

from __future__ import annotations

import logging
from typing import ClassVar, Self, cast

from src.services.base_service import BaseService
from src.services.core.embeddings_service import EmbeddingsService
from src.services.core.llm_service import LLMService
from src.services.core.rag_service import RAGService
from src.services.redis.txtai_service import TxtAIService


logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Registry for managing service instances.

    This class implements the singleton pattern to provide global access to service instances.
    It manages the lifecycle and access to all application services.

    Attributes:
        _instance: Singleton instance of the registry
        _services: Dictionary of registered services
    """

    _instance: ClassVar[ServiceRegistry | None] = None
    _services: ClassVar[dict[str, BaseService]] = {}

    def __new__(cls) -> Self:
        """Create or return singleton instance.

        Returns:
            ServiceRegistry: Singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cast(Self, cls._instance)

    @property
    def services(self) -> dict[str, BaseService]:
        """Get all registered services.

        Returns:
            dict[str, BaseService]: Dictionary of service instances
        """
        return self._services

    def get_service(self, name: str) -> BaseService | None:
        """Get a service by name.

        Args:
            name: Service name/key

        Returns:
            BaseService | None: Service instance if found, None otherwise
        """
        return self._services.get(name)

    @property
    def embeddings_service(self) -> EmbeddingsService | None:
        """Get embeddings service instance.

        Returns:
            EmbeddingsService | None: Service instance if registered and of correct type
        """
        service = self._services.get("embeddings")
        return service if isinstance(service, EmbeddingsService) else None

    @property
    def llm_service(self) -> LLMService | None:
        """Get LLM service instance.

        Returns:
            LLMService | None: Service instance if registered and of correct type
        """
        service = self._services.get("llm")
        return service if isinstance(service, LLMService) else None

    @property
    def rag_service(self) -> RAGService | None:
        """Get RAG service instance.

        Returns:
            RAGService | None: Service instance if registered and of correct type
        """
        service = self._services.get("rag")
        return service if isinstance(service, RAGService) else None

    @property
    def txtai_service(self) -> TxtAIService | None:
        """Get txtai service instance.

        Returns:
            TxtAIService | None: Service instance if registered and of correct type
        """
        service = self._services.get("txtai")
        return service if isinstance(service, TxtAIService) else None

    def register(self, name: str, service: BaseService) -> None:
        """Register a service instance.

        Args:
            name: Service name/key
            service: Service instance to register

        Raises:
            ValueError: If service name is empty or None
            TypeError: If service is not a BaseService instance
        """
        if not name:
            raise ValueError("Service name cannot be empty")
        if not isinstance(service, BaseService):
            raise TypeError(f"Service must be a BaseService instance, got {type(service)}")

        self._services[name] = service
        logger.info("Registered service: %s", name)

    def register_services(self, services: dict[str, BaseService]) -> None:
        """Register multiple services at once.

        Args:
            services: Dictionary of service instances to register

        Raises:
            ValueError: If services dict is empty
            TypeError: If any service is not a BaseService instance
        """
        if not services:
            raise ValueError("Services dictionary cannot be empty")

        for name, service in services.items():
            self.register(name, service)

    def unregister(self, name: str) -> None:
        """Unregister a service by name.

        Args:
            name: Service name/key to unregister
        """
        if name in self._services:
            del self._services[name]
            logger.info("Unregistered service: %s", name)

    async def check_health(self) -> dict[str, str]:
        """Check health of all registered services.

        Returns:
            dict[str, str]: Dictionary of service health statuses
        """
        health_status = {}
        for name, service in self._services.items():
            try:
                if not service.initialized:
                    health_status[name] = "not initialized"
                    continue

                # Add additional health checks here if needed
                health_status[name] = "healthy"
            except Exception as e:
                logger.error("Health check failed for service %s: %s", name, str(e))
                health_status[name] = f"unhealthy: {e!s}"

        return health_status


# Global registry instance
registry = ServiceRegistry()
