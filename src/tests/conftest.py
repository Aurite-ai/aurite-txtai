import pytest
import logging
import asyncio
from src.services import registry
from src.config.settings import Settings
from .fixtures.test_docs import get_test_documents
import os
from dotenv import load_dotenv

# Load environment variables at the top of conftest.py
load_dotenv()

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test settings with memory storage"""
    return Settings(
        EMBEDDINGS_STORAGE_TYPE="memory",
        EMBEDDINGS_CONTENT_PATH=":memory:",
        API_KEY="test-key",
        EMBEDDINGS_MODEL="sentence-transformers/nli-mpnet-base-v2",
        EMBEDDINGS_BATCH_SIZE=32,
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY"),
        SYSTEM_PROMPTS={
            "rag": "You are a helpful AI assistant.",
            "default": "You are a helpful AI assistant.",
        },
    )


@pytest.fixture(scope="session", autouse=True)
async def initialized_services(test_settings):
    """Initialize all services once for the test session"""
    logger.info("\n=== Initializing Services (Session) ===")
    try:
        registry.config_service.settings = test_settings
        await registry.config_service.initialize()
        await registry.embeddings_service.initialize()
        await registry.llm_service.initialize()
        await registry.rag_service.initialize()
        await registry.stream_service.initialize()
        await registry.communication_service.initialize()
        await registry.txtai_service.initialize()
        logger.info("All services initialized successfully")
        return registry
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        pytest.exit(f"Critical error: {e}", returncode=1)


@pytest.fixture(scope="function")
async def setup_test_data():
    """Setup test data using initialized services"""
    try:
        test_documents = get_test_documents()
        await registry.embeddings_service.add(test_documents)
        yield  # Use yield instead of return for proper cleanup
    finally:
        # Cleanup
        if registry.embeddings_service.initialized:
            delete_query = "DELETE FROM txtai"
            registry.embeddings_service.embeddings.delete(delete_query)
