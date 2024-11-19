import pytest
import json
import logging
from src.services import registry

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestEmbeddingsCore:
    """Test embeddings core functionality"""

    async def test_service_initialization(self, initialized_services, test_settings):
        """Test service initialization and configuration"""
        # Get initialized services
        services = await initialized_services

        # Verify service configuration
        assert services.embeddings_service.settings == test_settings
        assert services.embeddings_service.embeddings is not None
        assert (
            services.embeddings_service.embeddings.config["path"] == test_settings.EMBEDDINGS_MODEL
        )
        assert services.embeddings_service.embeddings.config["contentpath"] == ":memory:"

    @pytest.mark.asyncio
    async def test_document_operations(self, setup_test_data):
        """Test basic document operations"""
        test_doc = {
            "id": "test1",
            "text": "This is a test document about machine learning",
            "metadata": {"source": "test", "category": "tech"},
        }

        count = await registry.embeddings_service.add([test_doc])
        assert count == 1

        # Search for the document
        results = await registry.embeddings_service.hybrid_search("machine learning", limit=1)
        assert len(results) > 0
        assert "score" in results[0]
        assert "text" in results[0]
        assert "machine learning" in results[0]["text"].lower()

    @pytest.mark.asyncio
    async def test_empty_metadata_handling(self, initialized_services):
        """Test handling of documents with missing metadata"""
        minimal_docs = [
            {"id": "doc3", "text": "Test document with minimal metadata", "metadata": {}}
        ]

        count = await registry.embeddings_service.add(minimal_docs)
        assert count == 1

        results = registry.embeddings_service.embeddings.search("SELECT * FROM txtai")
        assert len(results) == 1
        assert json.loads(results[0]["tags"]) == {}

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in service operations"""
        # Create a new service instance for testing errors
        test_service = registry.embeddings_service.__class__()

        # Test operations without initialization
        with pytest.raises(ValueError, match=".*not initialized"):
            await test_service.add([])

        with pytest.raises(ValueError, match=".*not initialized"):
            await test_service.hybrid_search("test")

        # Test invalid document format with initialized service
        with pytest.raises(KeyError):
            await registry.embeddings_service.add([{"invalid": "document"}])

    @pytest.mark.asyncio
    async def test_batch_operations(self, setup_test_data):
        """Test batch document operations"""
        # Create multiple test documents
        batch_docs = [
            {
                "id": f"batch{i}",
                "text": f"Test document {i} about various topics",
                "metadata": {"batch": i},
            }
            for i in range(5)
        ]

        # Add batch
        count = await registry.embeddings_service.add(batch_docs)
        assert count == 5

        # Verify all documents were added
        results = registry.embeddings_service.embeddings.search(
            "SELECT COUNT(*) as count FROM txtai"
        )
        assert results[0]["count"] >= 5

    @pytest.mark.asyncio
    async def test_search_scoring(self, setup_test_data):
        """Test search result scoring"""
        # Add documents with varying relevance
        docs = [
            {
                "id": "relevant1",
                "text": "Machine learning is transforming artificial intelligence",
                "metadata": {"relevance": "high"},
            },
            {
                "id": "relevant2",
                "text": "Data science uses machine learning techniques",
                "metadata": {"relevance": "medium"},
            },
            {
                "id": "irrelevant",
                "text": "This document is about something else entirely",
                "metadata": {"relevance": "low"},
            },
        ]

        await registry.embeddings_service.add(docs)

        # Search and verify scoring
        results = await registry.embeddings_service.hybrid_search("machine learning", limit=3)
        assert len(results) == 3

        # Verify scores are in descending order
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

        # Verify most relevant document is first
        assert "machine learning" in results[0]["text"].lower()
