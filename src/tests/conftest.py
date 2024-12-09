from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv
import pytest

from src.config import Settings
from src.services import initialize_services

from .fixtures.test_docs import get_test_documents


# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for all tests"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def common_test_settings():
    """Common test settings used across test files"""
    return {
        "EMBEDDINGS_MODEL": "sentence-transformers/nli-mpnet-base-v2",
        "EMBEDDINGS_BATCH_SIZE": 32,
        "LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "SYSTEM_PROMPTS": {
            "rag": "You are a helpful AI assistant.",
            "default": "You are a helpful AI assistant.",
        },
    }


@pytest.fixture
def test_settings(common_test_settings):
    """Test settings for the application"""
    return Settings(
        EMBEDDINGS_CONTENT_PATH=":memory:",
        API_KEY="test-key",
        REDIS_DB=1,  # Use test database
        **common_test_settings,
    )


@pytest.fixture(scope="session")
async def initialized_services(event_loop, test_settings):
    """Initialize all services with test settings"""
    logger.info("\n=== Initializing Services (Session) ===")
    try:
        # Initialize all services
        services = await initialize_services(test_settings)
        logger.info("All services initialized successfully")
        yield services

        # Cleanup
        if services.get("stream"):
            await services["stream"].stop_listening()
        if services.get("communication"):
            await services["communication"].close()

    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise


@pytest.fixture
async def setup_test_data(initialized_services):
    """Setup test documents in embeddings service"""
    logger.info("\n=== Setting up Test Data ===")
    try:
        # Get test documents
        test_docs = get_test_documents()

        # Add documents to embeddings service
        embeddings_service = initialized_services["embeddings"]
        count = await embeddings_service.add(test_docs)
        logger.info(f"Added {count} test documents")

        yield test_docs

    except Exception as e:
        logger.error(f"Test data setup failed: {e}")
        raise
