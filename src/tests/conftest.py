import pytest
from pathlib import Path
import json
from src.services.embeddings_service import embeddings_service
from src.services.txtai_service import txtai_service
from src.config.settings import Settings


@pytest.fixture(scope="session")
def test_settings():
    """Test settings with memory storage"""
    return Settings(
        EMBEDDINGS_STORAGE_TYPE="memory",
        EMBEDDINGS_CONTENT_PATH=":memory:",
        API_KEY="test-key",
        EMBEDDINGS_MODEL="sentence-transformers/nli-mpnet-base-v2",
        EMBEDDINGS_BATCH_SIZE=32,
    )


@pytest.fixture(scope="session")
def test_documents():
    """Test documents with metadata matching notebook format"""
    return [
        {
            "id": "doc1",
            "text": "Machine learning models require significant computational resources",
            "metadata": {
                "category": "tech",
                "tags": ["ML", "computing"],
                "priority": 1,
            },
        },
        {
            "id": "doc2",
            "text": "Natural language processing advances with transformer models",
            "metadata": {"category": "tech", "tags": ["NLP", "ML"], "priority": 2},
        },
    ]


@pytest.fixture(scope="session")
async def base_services(test_settings):
    """Initialize base services for all tests"""
    try:
        # Initialize txtai service (which handles embeddings and RAG)
        await txtai_service.initialize()
        yield
    finally:
        # Cleanup if needed
        pass


@pytest.fixture(scope="function")
async def setup_services(base_services, test_documents):
    """Setup test data for each test"""
    try:
        # Reset embeddings index before adding test data
        await embeddings_service.initialize()
        # Add test documents
        await embeddings_service.add(test_documents)
        yield
    except Exception as e:
        pytest.fail(f"Failed to setup test data: {e}")


@pytest.fixture(scope="function")
async def clean_services(setup_services):
    """Cleanup after each test"""
    yield
    try:
        # Reset embeddings index
        await embeddings_service.initialize()
    except Exception as e:
        pytest.fail(f"Failed to clean services: {e}")
