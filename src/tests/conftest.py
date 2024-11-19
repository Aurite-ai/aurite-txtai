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
    """Create a single event loop for all tests"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
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
        REDIS_DB=1,  # Use test database
    )


@pytest.fixture(scope="session")
async def redis_client(event_loop, test_settings):
    """Create a Redis client for tests"""
    import redis.asyncio as redis

    client = redis.Redis(
        host=test_settings.REDIS_HOST,
        port=test_settings.REDIS_PORT,
        db=test_settings.REDIS_DB,
        decode_responses=True,
        single_connection_client=True,
    )
    await client.ping()  # Test connection
    yield client
    await client.close()


@pytest.fixture(scope="session")
async def initialized_services(event_loop, test_settings, redis_client):
    """Initialize all services with test settings"""
    logger.info("\n=== Initializing Services (Session) ===")
    try:
        # Set event loop for the entire initialization process
        asyncio.set_event_loop(event_loop)

        registry.config_service.settings = test_settings
        await registry.config_service.initialize()

        # Set Redis client before other services
        registry.communication_service._redis_client = redis_client

        # Initialize services
        await registry.embeddings_service.initialize()
        await registry.llm_service.initialize()
        await registry.rag_service.initialize()
        await registry.communication_service.initialize()
        await registry.stream_service.initialize()
        await registry.txtai_service.initialize()

        logger.info("All services initialized successfully")
        return registry
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        pytest.exit(f"Critical error: {e}", returncode=1)


@pytest.fixture(autouse=True)
async def clean_redis(redis_client):
    """Clean Redis before and after each test"""
    await redis_client.flushdb()
    yield
    await redis_client.flushdb()
