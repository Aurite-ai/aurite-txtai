from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar


if TYPE_CHECKING:
    from src.config import Settings


logger = logging.getLogger(__name__)


T = TypeVar("T", bound="BaseService")


class BaseService(ABC):
    """Base class for all services.

    This class provides the foundation for all services in the application.
    It enforces initialization patterns and settings management.

    Attributes:
        _initialized: Whether the service has been initialized
        _settings: Application settings instance
    """

    def __init__(self) -> None:
        """Initialize base service with default state."""
        self._initialized: bool = False
        self._settings: Settings | None = None

    @property
    def initialized(self) -> bool:
        """Check if service is initialized.

        Returns:
            bool: True if service is initialized, False otherwise
        """
        return self._initialized

    @property
    def settings(self) -> Settings:
        """Get settings, raising an error if not initialized.

        Returns:
            Settings: Application settings instance

        Raises:
            RuntimeError: If settings are not initialized
        """
        if self._settings is None:
            raise RuntimeError(f"{self.__class__.__name__} settings not initialized")
        return self._settings

    def _check_initialized(self) -> None:
        """Check if service is initialized and raise error if not.

        Raises:
            RuntimeError: If service is not initialized
        """
        if not self._initialized:
            raise RuntimeError(f"{self.__class__.__name__} not initialized")

    @abstractmethod
    async def initialize(self: T, settings: Settings, **kwargs: Any) -> None:
        """Initialize the service with the provided configuration.

        This method must be implemented by all service classes to handle
        their specific initialization requirements.

        Args:
            settings: Application settings
            **kwargs: Additional service-specific configuration

        Raises:
            NotImplementedError: If not implemented by subclass
            RuntimeError: If service is already initialized
            Exception: If initialization fails
        """
        if self._initialized:
            raise RuntimeError(f"{self.__class__.__name__} already initialized")
        self._settings = settings
