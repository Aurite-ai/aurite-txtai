import pytest
from pathlib import Path
from src.config.settings import Settings


@pytest.fixture
def test_settings():
    """Provide test settings with memory storage"""
    return Settings(
        EMBEDDINGS_MODEL="sentence-transformers/nli-mpnet-base-v2",
        EMBEDDINGS_STORAGE_TYPE="memory",
        EMBEDDINGS_CONTENT_PATH=":memory:",
        EMBEDDINGS_PREFIX="test",
    )


@pytest.fixture
def test_documents():
    """Provide test documents for embeddings"""
    return [
        {
            "id": "test1",
            "text": "Technical document about machine learning",
            "metadata": {"type": "technical", "tags": ["ML", "AI"]},
        },
        {
            "id": "test2",
            "text": "Guide to cloud storage systems",
            "metadata": {"type": "guide", "tags": ["cloud", "storage"]},
        },
    ]
