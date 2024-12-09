"""Redis stream service initialization"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

from .communication_service import communication_service
from .stream_service import stream_service
from .txtai_service import txtai_service


if TYPE_CHECKING:
    from src.config import Settings


logger = logging.getLogger(__name__)


async def initialize_redis_services(
    settings: Settings, core_services: dict[str, Any]
) -> dict[str, Any]:
    """Initialize Redis services"""
    try:
        logger.info("Initializing Redis communication service...")
        await communication_service.initialize(settings)
        logger.info("Initializing txtai service...")
        await txtai_service.initialize(settings=settings, services=core_services)
        logger.info("Initializing stream service...")
        await stream_service.initialize(settings, communication_service, txtai_service)

        return {
            "communication": communication_service,
            "txtai": txtai_service,
            "stream": stream_service,
        }
    except Exception as e:
        logger.error(f"Redis service initialization failed: {e}")
        raise


# Export services
__all__ = ["communication_service", "initialize_redis_services", "stream_service", "txtai_service"]
