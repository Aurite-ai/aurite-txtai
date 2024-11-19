import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base class for all services"""

    def __init__(self):
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized

    @abstractmethod
    async def initialize(self):
        """Initialize the service"""
        pass

    def _check_initialized(self):
        """Check if service is initialized and raise error if not"""
        if not self._initialized:
            raise ValueError(f"{self.__class__.__name__} not initialized")
