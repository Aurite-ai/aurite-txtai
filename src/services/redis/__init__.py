"""Redis stream service initialization"""

import logging
from typing import Dict, Any
from src.config import Settings
from .communication_service import communication_service
from .stream_service import stream_service
from .txtai_service import txtai_service

logger = logging.getLogger(__name__)


async def initialize_redis_services(
    settings: Settings, core_services: Dict[str, Any]
) -> Dict[str, Any]:
    """Initialize Redis services in correct order"""
    try:
        # Initialize base communication service first
        logger.info("Initializing Redis communication service...")
        await communication_service.initialize(settings)

        # Initialize txtai service with core services
        logger.info("Initializing txtai service...")
        await txtai_service.initialize(services=core_services)

        # Initialize stream service last
        logger.info("Initializing stream service...")
        await stream_service.initialize(settings)

        return {
            "communication": communication_service,
            "txtai": txtai_service,
            "stream": stream_service,
        }

    except Exception as e:
        logger.error(f"Redis service initialization failed: {e}")
        raise


# Export services
__all__ = ["communication_service", "stream_service", "txtai_service", "initialize_redis_services"]