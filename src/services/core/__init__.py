"""Core service initialization"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

from .embeddings_service import embeddings_service
from .llm_service import llm_service
from .rag_service import rag_service


if TYPE_CHECKING:
    from src.config import Settings


logger = logging.getLogger(__name__)


async def initialize_core_services(settings: Settings) -> dict[str, Any]:
    """Initialize core services in correct order"""
    try:
        # Initialize base services in parallel since they're independent
        logger.info("Initializing embeddings and LLM services...")
        await embeddings_service.initialize(settings)
        await llm_service.initialize(settings)

        # Initialize RAG service after dependencies are ready
        logger.info("Initializing RAG service...")
        await rag_service.initialize(settings, embeddings_service, llm_service)

        return {"embeddings": embeddings_service, "llm": llm_service, "rag": rag_service}

    except Exception as e:
        logger.error(f"Core service initialization failed: {e}")
        raise


# Export services
__all__ = ["embeddings_service", "initialize_core_services", "llm_service", "rag_service"]
