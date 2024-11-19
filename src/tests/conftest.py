import pytest
import logging
import asyncio
from src.services import registry
from src.config.settings import Settings
from .fixtures.test_docs import get_test_documents
import os
from dotenv import load_dotenv

# Load environment variables
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
        # Redis test settings
        REDIS_DB=1,  # Use separate test database
    )


@pytest.fixture(scope="session", autouse=True)
async def initialized_services(test_settings):
    """Initialize all services once for the test session"""
    logger.info("\n=== Initializing Services (Session) ===")
    try:
        # Initialize in correct order
        registry.config_service.settings = test_settings
        await registry.config_service.initialize()

        # Initialize core services first
        await registry.embeddings_service.initialize()
        await registry.llm_service.initialize()
        await registry.rag_service.initialize()

        # Initialize communication services
        await registry.communication_service.initialize()
        await registry.stream_service.initialize()

        # Initialize composite services
        await registry.txtai_service.initialize()

        logger.info("All services initialized successfully")
        return registry
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        pytest.exit(f"Critical error: {e}", returncode=1)


@pytest.fixture(autouse=True)
async def clean_redis(initialized_services):
    """Clean Redis before and after each test"""
    redis_client = registry.communication_service._redis_client
    try:
        # Clean before test
        await redis_client.flushdb()
        yield
    finally:
        # Clean after test
        await redis_client.flushdb()
