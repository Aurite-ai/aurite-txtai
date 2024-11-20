"""Core service initialization"""

import logging
from typing import Dict, Any
from settings import Settings
from .embeddings_service import embeddings_service
from .llm_service import llm_service
from .rag_service import rag_service

logger = logging.getLogger(__name__)


async def initialize_core_services(settings: Settings) -> Dict[str, Any]:
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
__all__ = ["embeddings_service", "llm_service", "rag_service", "initialize_core_services"]
