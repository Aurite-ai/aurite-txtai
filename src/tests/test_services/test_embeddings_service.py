import pytest
from pathlib import Path
from src.services.embeddings_service import EmbeddingsService
import logging
import json
from src.services.config_service import config_service

logger = logging.getLogger(__name__)


class TestEmbeddingsStorage:
    """Test embeddings storage operations"""

    def test_constructor_with_settings(self, test_settings):
        """Test constructor with settings parameter"""
        service = EmbeddingsService(test_settings)
        assert service.settings == test_settings
        assert service.embeddings is not None  # Should auto-initialize

    def test_constructor_without_settings(self):
        """Test constructor without settings parameter"""
        service = EmbeddingsService()
        assert service.settings == config_service.settings
        assert service.embeddings is None  # Should not auto-initialize

    def test_memory_storage(self, test_settings, test_documents):
        """Test memory storage operations"""
        service = EmbeddingsService(test_settings)

        # Add test documents
        count = service.add(test_documents)
        assert count == len(test_documents)
        assert service.embeddings is not None

        # Verify storage type
        assert service.embeddings.config.get("contentpath") == ":memory:"

    def test_persistence(self, test_settings, test_documents, tmp_path):
        """Test index persistence operations"""
        # Create and populate first service
        service1 = EmbeddingsService(test_settings)
        service1.add(test_documents)

        # Save index
        save_path = tmp_path / "test_index"
        service1.embeddings.save(str(save_path))

        # Create new service and load index
        service2 = EmbeddingsService(test_settings)
        service2.embeddings.load(str(save_path))

        # Verify documents were preserved
        results = service2.embeddings.search("SELECT COUNT(*) as count FROM txtai")
        assert results[0]["count"] == len(test_documents)

    def test_error_handling(self, test_settings):
        """Test error handling"""
        service = EmbeddingsService()  # Don't initialize

        # Test operations without initialization
        with pytest.raises(ValueError, match="Embeddings not initialized"):
            service.add([])


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
        sql_results = service.embeddings.search("SELECT id, text, tags FROM txtai")
        assert len(sql_results) == len(test_documents)

        # Verify metadata storage
        for doc in sql_results:
            assert "tags" in doc
            metadata = json.loads(doc["tags"])
            assert "category" in metadata
            assert metadata["category"] == "tech"

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

    def test_metadata_filtering(self, test_settings, test_documents):
        """Test metadata-based filtering"""
        service = EmbeddingsService()
        service.initialize()
        service.add(test_documents)

        # SQL query with metadata filter using tags column
        # Use single quotes for SQL and double quotes for JSON pattern - no escaping needed
        sql_query = """
            SELECT id, text, tags
            FROM txtai
            WHERE tags LIKE '%"category":"tech"%'
            ORDER BY id
        """
        results = service.embeddings.search(sql_query)

        # All test documents should have tech category
        assert len(results) == len(test_documents)

        # Verify each result has correct metadata
        for result in results:
            metadata = json.loads(result["tags"])
            assert metadata["category"] == "tech"
            assert "tags" in metadata  # Should have tags array
            assert isinstance(metadata["tags"], list)  # Tags should be a list
            assert "priority" in metadata  # Should have priority field

    def test_document_retrieval(self, test_settings, test_documents):
        """Test document retrieval with complete metadata"""
        service = EmbeddingsService()
        service.initialize()
        service.add(test_documents)

        # Get specific document
        doc_id = test_documents[0]["id"]
        sql_query = f"""
            SELECT id, text, tags
            FROM txtai
            WHERE id = '{doc_id}'
        """
        results = service.embeddings.search(sql_query)

        assert len(results) == 1
        result = results[0]

        # Verify document content
        assert result["id"] == doc_id
        assert result["text"] == test_documents[0]["text"]

        # Verify complete metadata structure
        metadata = json.loads(result["tags"])
        original_metadata = test_documents[0]["metadata"]
        assert metadata == original_metadata

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
        assert best_match["score"] > 0.5  # Reasonable similarity threshold
