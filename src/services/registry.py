"""Service registry for accessing initialized services"""

from typing import Dict, Any, Optional
from .base_service import BaseService


class ServiceRegistry:
    """Registry for accessing initialized services"""

    _instance = None
    _services: Dict[str, BaseService] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
        return cls._instance

    @property
    def embeddings_service(self):
        return self._services.get("embeddings")

    @property
    def llm_service(self):
        return self._services.get("llm")

    @property
    def rag_service(self):
        return self._services.get("rag")

    @property
    def txtai_service(self):
        return self._services.get("txtai")

    def register_services(self, services: Dict[str, Any]) -> None:
        """Register all services"""
        self._services = services


# Global instance
registry = ServiceRegistry()
