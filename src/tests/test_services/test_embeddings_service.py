from __future__ import annotations

import json
import logging
from typing import Any

import pytest

from src.models.txtai_types import EmbeddingsDocument, EmbeddingsResult
from src.services import registry
from src.tests.fixtures.test_docs import get_test_documents


logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
async def cleanup_database():
    """Reset the database before each test"""
    # Run the test
    yield

    # Clean up after test
    if registry.embeddings_service.embeddings is not None:
        # Just reinitialize the embeddings to clear the database
        registry.embeddings_service.embeddings.index([])


@pytest.fixture
def test_documents() -> list[EmbeddingsDocument]:
    """Fixture for test documents"""
    return [
        {
            "id": "doc1",
            "text": "Machine learning and artificial intelligence are transforming technology",
            "metadata": {"relevance": "high", "category": "tech"},
        },
        {
            "id": "doc2",
            "text": "Data science uses statistical and machine learning techniques",
            "metadata": {"relevance": "medium", "category": "tech"},
        },
        {
            "id": "doc3",
            "text": "Cloud computing enables scalable infrastructure",
            "metadata": {"relevance": "low", "category": "tech"},
        },
    ]


@pytest.mark.asyncio
class TestEmbeddingsCore:
    """Test embeddings core functionality"""

    async def test_service_initialization(self, initialized_services, test_settings) -> None:
        """Test service initialization and configuration"""
        assert registry.embeddings_service.initialized
        assert registry.embeddings_service.embeddings is not None

        # Verify configuration matches settings
        config = registry.embeddings_service.embeddings.config
        assert config["path"] == test_settings.EMBEDDINGS_MODEL
        assert config["contentpath"] == test_settings.EMBEDDINGS_CONTENT_PATH
        assert config["batch"] == test_settings.EMBEDDINGS_BATCH_SIZE
        assert config["hybrid"] is True
        assert config["normalize"] is True

        # Verify scoring configuration
        assert config["scoring"]["method"] == "bm25"
        assert config["scoring"]["weights"] == {"hybrid": 0.7, "terms": 0.3}

    async def test_document_operations(self, setup_test_data) -> None:
        """Test basic document operations"""
        test_doc: EmbeddingsDocument = {
            "id": "test1",
            "text": "This is a test document about machine learning",
            "metadata": {"source": "test", "category": "tech"},
        }

        # Add document
        count = await registry.embeddings_service.add([test_doc])
        assert count == 1

        # Search for the document
        results = await registry.embeddings_service.hybrid_search("machine learning", limit=1)
        assert len(results) > 0

        # Get document by ID to verify metadata
        sql_results = registry.embeddings_service.embeddings.search(
            "SELECT id, text, tags FROM txtai WHERE id = 'test1'"
        )
        assert len(sql_results) == 1
        result = sql_results[0]
        assert result["id"] == test_doc["id"]
        assert result["text"] == test_doc["text"]
        assert json.loads(result["tags"]) == test_doc["metadata"]

    async def test_metadata_handling(self) -> None:
        """Test various metadata scenarios"""
        docs: list[EmbeddingsDocument] = [
            {
                "id": "meta1",
                "text": "Document with full metadata",
                "metadata": {"source": "test", "tags": ["a", "b"], "priority": 1},
            },
            {
                "id": "meta2",
                "text": "Document with minimal metadata",
                "metadata": {},
            },
            {
                "id": "meta3",
                "text": "Document with nested metadata",
                "metadata": {"nested": {"key": "value"}, "array": [1, 2, 3]},
            },
        ]

        # Add documents
        count = await registry.embeddings_service.add(docs)
        assert count == 3

        # Verify metadata handling
        results = registry.embeddings_service.embeddings.search(
            "SELECT id, text, tags FROM txtai WHERE id IN ('meta1', 'meta2', 'meta3')"
        )
        assert len(results) == 3

        # Check metadata serialization/deserialization
        for result in results:
            metadata = json.loads(result["tags"])
            if result["id"] == "meta1":
                assert "tags" in metadata
                assert isinstance(metadata["tags"], list)
                assert metadata["priority"] == 1
            elif result["id"] == "meta2":
                assert metadata == {}
            elif result["id"] == "meta3":
                assert isinstance(metadata["nested"], dict)
                assert metadata["nested"]["key"] == "value"
                assert isinstance(metadata["array"], list)
                assert metadata["array"] == [1, 2, 3]

    async def test_error_handling(self, initialized_services) -> None:
        """Test error handling in service operations"""
        # Test uninitialized service
        from src.services.core.embeddings_service import EmbeddingsService

        test_service = EmbeddingsService()
        with pytest.raises((RuntimeError, ValueError), match=".*not initialized"):
            await test_service.add([])
        with pytest.raises((RuntimeError, ValueError), match=".*not initialized"):
            await test_service.hybrid_search("test")

        # Test invalid document format
        embeddings_service = initialized_services["embeddings"]
        with pytest.raises(KeyError):
            await embeddings_service.add([{"invalid": "document"}])  # type: ignore

        # Add some test documents for search tests
        test_docs = get_test_documents()
        await embeddings_service.add(test_docs)

        # Test empty query
        results = await embeddings_service.hybrid_search("")
        assert len(results) == 0

        # Test invalid score threshold
        results = await embeddings_service.hybrid_search("test", min_score=2.0)
        assert len(results) == 0  # No results should match such a high score threshold

        # Test invalid document fields
        invalid_docs: list[Any] = [
            {"id": "test", "metadata": {}},  # Missing text
            {"text": "test", "metadata": {}},  # Missing id
            {"id": "test", "text": "test"},  # Missing metadata
            {"id": None, "text": "test", "metadata": {}},  # Invalid id type
            {"id": "test", "text": None, "metadata": {}},  # Invalid text type
            {"id": "test", "text": "test", "metadata": None},  # Invalid metadata type
        ]
        for doc in invalid_docs:
            with pytest.raises((KeyError, TypeError)):
                await embeddings_service.add([doc])  # type: ignore

    async def test_batch_operations(self) -> None:
        """Test batch document operations"""
        # Create test documents
        batch_docs = [
            {
                "id": f"batch{i}",
                "text": f"Test document {i} about various topics",
                "metadata": {"batch": i, "category": "test"},
            }
            for i in range(5)
        ]

        # Add batch
        count = await registry.embeddings_service.add(batch_docs)
        assert count == 5

        # Verify all documents were added using COUNT
        count_results = registry.embeddings_service.embeddings.search("SELECT COUNT(*) as count FROM txtai")
        assert count_results[0]["count"] == 5

        # Verify all documents were added with full query
        results = registry.embeddings_service.embeddings.search(
            "SELECT id, text, tags FROM txtai ORDER BY id LIMIT 1000"
        )
        assert len(results) == 5

        # Verify document content and metadata
        for i, result in enumerate(results):
            metadata = json.loads(result["tags"])
            assert metadata["category"] == "test"
            assert metadata["batch"] == i
            assert result["id"] == f"batch{i}"
            assert result["text"] == f"Test document {i} about various topics"

        # Verify document content through hybrid search
        for i in range(5):
            results = await registry.embeddings_service.hybrid_search(f"document {i}", limit=1)
            assert len(results) == 1
            assert results[0]["id"] == f"batch{i}"
            assert results[0]["metadata"]["batch"] == i

    async def test_search_functionality(self, test_documents) -> None:
        """Test various search scenarios"""
        # Add test documents
        await registry.embeddings_service.add(test_documents)

        # Test semantic search
        results = await registry.embeddings_service.hybrid_search("AI and ML", limit=2)
        assert len(results) == 2
        assert "machine learning" in results[0]["text"].lower()

        # Test exact phrase matching
        results = await registry.embeddings_service.hybrid_search('"machine learning"', limit=2)
        assert len(results) == 2
        assert all("machine learning" in r["text"].lower() for r in results)

        # Test with minimum score threshold
        results = await registry.embeddings_service.hybrid_search("technology", min_score=0.5, limit=3)
        assert all(r["score"] >= 0.5 for r in results)

        # Verify score ordering
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

        # Test metadata filtering
        high_relevance = registry.embeddings_service.embeddings.search(
            "SELECT id, text, tags FROM txtai WHERE tags LIKE '%high%'"
        )
        assert len(high_relevance) == 1
        metadata = json.loads(high_relevance[0]["tags"])
        assert metadata["relevance"] == "high"

    async def test_database_verification(self) -> None:
        """Test database verification functionality"""
        # Add some documents
        docs: list[EmbeddingsDocument] = [
            {
                "id": "verify1",
                "text": "Test document for verification",
                "metadata": {"test": "verify"},
            }
        ]
        await registry.embeddings_service.add(docs)

        # Verify count
        count = await registry.embeddings_service.verify_database()
        assert count > 0

        # Test with uninitialized service
        test_service = registry.embeddings_service.__class__()
        with pytest.raises((RuntimeError, ValueError), match=".*not initialized"):
            await test_service.verify_database()

    def _verify_search_result(self, result: EmbeddingsResult, original: EmbeddingsDocument) -> None:
        """Helper to verify search result matches original document"""
        assert result["id"] == original["id"]
        assert result["text"] == original["text"]
        assert isinstance(result["score"], float)
        assert 0 <= result["score"] <= 1.0
        assert result["metadata"] == original["metadata"]
