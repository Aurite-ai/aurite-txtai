"""Service initialization and registry for txtai services"""

import logging
from typing import Dict, Any
from settings import Settings
from .core import initialize_core_services
from .redis import initialize_redis_services

logger = logging.getLogger(__name__)


async def initialize_services(settings: Settings) -> Dict[str, Any]:
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

        # Return combined services
        return {**core_services, **redis_services}

    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise


# Export initialization function
__all__ = ["initialize_services"]
