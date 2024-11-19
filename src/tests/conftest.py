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
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
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


@pytest.fixture(scope="session")
async def initialized_services(test_settings):
    """Initialize all services once for the test session"""
    logger.info("\n=== Initializing Services (Session) ===")
    try:
        # Initialize config service first
        registry.config_service.settings = test_settings
        await registry.config_service.initialize()
        logger.info("Config service initialized")

        # Initialize embeddings service
        await registry.embeddings_service.initialize()
        logger.info("Embeddings service initialized")

        # Initialize LLM service
        await registry.llm_service.initialize()
        logger.info("LLM service initialized")

        # Initialize RAG service
        await registry.rag_service.initialize()
        logger.info("RAG service initialized")

        # Initialize Stream service
        await registry.stream_service.initialize()
        logger.info("Stream service initialized")

        # Initialize Communication service
        await registry.communication_service.initialize()
        logger.info("Communication service initialized")

        # Initialize TxtAI service
        await registry.txtai_service.initialize()
        logger.info("TxtAI service initialized")

        logger.info("All services initialized successfully")
        return registry

    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        pytest.exit(f"Critical error: {e}", returncode=1)


@pytest.fixture(scope="function")
async def setup_test_data():
    """Setup test data using initialized services"""
    logger.info("\n=== Setting up test data ===")
    try:
        # Get test documents
        test_documents = get_test_documents()
        logger.info(f"Got {len(test_documents)} test documents")

        # Add documents
        logger.info("Adding documents to embeddings service...")
        await registry.embeddings_service.add(test_documents)
        logger.info("Documents added to embeddings service")

        # Verify documents were added
        verify_query = "SELECT COUNT(*) as count FROM txtai"
        logger.info(f"Verifying documents with query: {verify_query}")
        results = registry.embeddings_service.embeddings.search(verify_query)
        count = results[0]["count"] if results else 0
        logger.info(f"Found {count} documents in index")

        # Show sample document
        if count > 0:
            sample_query = "SELECT id, text FROM txtai LIMIT 1"
            sample = registry.embeddings_service.embeddings.search(sample_query)
            logger.info(f"Sample document: {sample[0]}")

        assert count == len(
            test_documents
        ), f"Expected {len(test_documents)} documents, got {count}"
        logger.info("Test data setup complete")

        yield

    except Exception as e:
        logger.error(f"Test data setup failed: {e}")
        pytest.fail(f"Test data setup failed: {e}")
