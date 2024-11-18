import pytest
from src.services.embeddings_service import EmbeddingsService
from src.services.query_service import QueryService
from src.config.settings import Settings
import json
import os


@pytest.fixture
def test_settings():
    """Test settings with memory storage"""
    return Settings(
        EMBEDDINGS_STORAGE_TYPE="memory",
        EMBEDDINGS_CONTENT_PATH="txtai/test/content.db",
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
def test_services(test_settings, test_documents):
    """Create test instances of embeddings and query services"""
    embeddings_service = EmbeddingsService(test_settings)
    embeddings_service.create_index()

    # Add documents using the service method instead of direct indexing
    embeddings_service.add_documents(test_documents)

    query_service = QueryService(embeddings_service.embeddings, test_settings)
    return embeddings_service, query_service
