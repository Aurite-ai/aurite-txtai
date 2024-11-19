import logging
from typing import Optional
from src.config.settings import Settings

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class"""

    def __init__(self):
        """Initialize base service"""
        self._initialized = False
        self.settings: Optional[Settings] = None
        from .config_service import config_service

        self.config_service = config_service

    @property
    def initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized

    def _check_initialized(self):
        """Check if service is initialized and raise error if not"""
        if not self._initialized:
            raise ValueError(f"{self.__class__.__name__} not initialized")

    async def initialize(self) -> None:
        """Initialize service - to be implemented by child classes"""
        raise NotImplementedError("Service must implement initialize method")
