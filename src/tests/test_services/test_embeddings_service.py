import pytest
import json
import logging
from pathlib import Path

from src.services.embeddings_service import EmbeddingsService

logger = logging.getLogger(__name__)


class TestEmbeddingsCore:
    """Test core embeddings functionality"""

    def test_document_indexing(self, test_settings, test_documents):
        """Test basic document indexing with metadata"""
        service = EmbeddingsService()
        service.initialize()

        # Add test documents
        count = service.add(test_documents)
        assert count == len(test_documents)

        # Verify documents were indexed
        sql_query = '''
            SELECT id, text, tags
            FROM txtai
        '''
        results = service.embeddings.search(sql_query)
        assert len(results) == len(test_documents)

        # Verify metadata storage
        for doc in results:
            assert "tags" in doc
            metadata = json.loads(doc["tags"])
            assert "category" in metadata
            assert metadata["category"] == "tech"

    def test_metadata_filtering(self, test_settings, test_documents):
        """Test metadata-based filtering"""
        service = EmbeddingsService()
        service.initialize()
        service.add(test_documents)

        # SQL query with metadata filter using tags column
        sql_query = '''
            SELECT id, text, tags
            FROM txtai
            WHERE tags LIKE '%"category": "tech"%'
            ORDER BY id
        '''
        results = service.embeddings.search(sql_query)

        # All test documents should have tech category
        assert len(results) == len(test_documents)

        # Verify each result has correct metadata
        for result in results:
            metadata = json.loads(result["tags"])
            assert metadata["category"] == "tech"
            assert "tags" in metadata
            assert isinstance(metadata["tags"], list)
            assert "priority" in metadata

    def test_hybrid_search(self, test_settings, test_documents):
        """Test hybrid search with metadata"""
        service = EmbeddingsService()
        service.initialize()
        service.add(test_documents)

        # Perform search
        results = service.hybrid_search("machine learning", limit=2)

        # Verify results structure
        assert len(results) > 0
        first_result = results[0]
        assert all(k in first_result for k in ["id", "text", "score", "metadata"])

        # Verify metadata is present and correct
        assert first_result["metadata"]["category"] == "tech"
        assert "tags" in first_result["metadata"]
        assert isinstance(first_result["metadata"]["tags"], list)

    def test_search_ranking(self, test_settings, test_documents):
        """Test search result ranking and scores"""
        service = EmbeddingsService()
        service.initialize()
        service.add(test_documents)

        # Search for specific term
        results = service.hybrid_search("machine learning")

        # Verify score ordering
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

        # Verify best match
        best_match = results[0]
        assert "machine learning" in best_match["text"].lower()
        assert best_match["score"] > 0.5

    def test_metadata_complex_filtering(self, test_settings, test_documents):
        """Test complex metadata filtering with multiple conditions"""
        service = EmbeddingsService()
        service.initialize()
        service.add(test_documents)

        # SQL query with multiple metadata conditions
        sql_query = '''
            SELECT id, text, tags
            FROM txtai
            WHERE tags LIKE '%"category": "tech"%'
            AND tags LIKE '%"priority": 1%'
            ORDER BY id
        '''
        results = service.embeddings.search(sql_query)

        # Verify filtered results
        assert len(results) == 1  # Only one document should match both conditions
        metadata = json.loads(results[0]["tags"])
        assert metadata["category"] == "tech"
        assert metadata["priority"] == 1

    def test_tag_based_search(self, test_settings, test_documents):
        """Test searching by specific tags in metadata"""
        service = EmbeddingsService()
        service.initialize()
        service.add(test_documents)

        # Search for documents with specific tag
        sql_query = '''
            SELECT id, text, tags
            FROM txtai
            WHERE tags LIKE '%"ML"%'
            ORDER BY id
        '''
        results = service.embeddings.search(sql_query)

        # Both documents should have ML tag
        assert len(results) == 2
        for result in results:
            metadata = json.loads(result["tags"])
            assert "ML" in metadata["tags"]

    def test_document_initialization(self, test_settings):
        """Test service initialization and configuration"""
        service = EmbeddingsService(test_settings)

        # Verify service configuration
        assert service.settings == test_settings
        assert service.embeddings is not None
        assert service.embeddings.config["path"] == test_settings.EMBEDDINGS_MODEL
        assert service.embeddings.config["contentpath"] == ":memory:"

    def test_empty_metadata_handling(self, test_settings):
        """Test handling of documents with missing metadata"""
        service = EmbeddingsService()
        service.initialize()

        # Document with minimal metadata
        minimal_docs = [
            {"id": "doc3", "text": "Test document with minimal metadata", "metadata": {}}
        ]

        # Should handle empty metadata without error
        count = service.add(minimal_docs)
        assert count == 1

        # Verify storage
        results = service.embeddings.search("SELECT * FROM txtai")
        assert len(results) == 1
        assert json.loads(results[0]["tags"]) == {}

    def test_error_handling(self, test_settings):
        """Test error handling in service operations"""
        service = EmbeddingsService()

        # Test operations without initialization
        with pytest.raises(ValueError, match="Embeddings not initialized"):
            service.add([])

        with pytest.raises(ValueError, match="Embeddings not initialized"):
            service.hybrid_search("test")

        # Test invalid document format
        service.initialize()
        with pytest.raises(KeyError):
            service.add([{"invalid": "document"}])
