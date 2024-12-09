"""Service initialization and registry for txtai services"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

from .core import initialize_core_services
from .redis import initialize_redis_services
from .registry import registry


if TYPE_CHECKING:
    from src.config import Settings


logger = logging.getLogger(__name__)


async def initialize_services(settings: Settings) -> dict[str, Any]:
    """Initialize all services in correct order"""
    try:
        # Initialize core services first
        logger.info("Initializing core services...")
        core_services = await initialize_core_services(settings)
        logger.info("Core services initialized successfully")

        # Initialize redis services with core services
        logger.info("Initializing redis services...")
        redis_services = await initialize_redis_services(settings, core_services)
        logger.info("Redis services initialized successfully")

        # Combine services and register them
        services = {**core_services, **redis_services}
        registry.register_services(services)

        return services

    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise


# Export initialization function and registry
__all__ = ["initialize_services", "registry"]
