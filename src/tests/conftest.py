import pytest
from pathlib import Path
import json
from src.services.embeddings_service import EmbeddingsService
from src.services.query_service import QueryService
from src.config.settings import Settings
from src.config.txtai_config import create_embeddings_config


@pytest.fixture
def test_settings():
    """Test settings with memory storage"""
    return Settings(
        EMBEDDINGS_STORAGE_TYPE="memory",
        EMBEDDINGS_CONTENT_PATH=":memory:",
        API_KEY="test-key",
        EMBEDDINGS_MODEL="sentence-transformers/nli-mpnet-base-v2",
        EMBEDDINGS_BATCH_SIZE=32,
    )


@pytest.fixture
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


@pytest.fixture
def test_embeddings_config(test_settings):
    """Create test embeddings configuration"""
    return create_embeddings_config(test_settings)


@pytest.fixture
def test_services(test_settings, test_documents):
    """Create test instances of embeddings and query services"""
    # Create and initialize embeddings service
    embeddings_service = EmbeddingsService()
    embeddings_service.initialize()

    # Add test documents
    embeddings_service.add(test_documents)

    # Create query service
    query_service = QueryService(embeddings_service.embeddings, test_settings)

    return embeddings_service, query_service
