import logging
from typing import Optional
from abc import ABC

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base class for all services"""

    def __init__(self):
        """Initialize base service"""
        self._initialized: bool = False

    @property
    def initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized

    def _check_initialized(self) -> None:
        """Check if service is initialized and raise error if not"""
        if not self._initialized:
            raise RuntimeError(f"{self.__class__.__name__} not initialized")
