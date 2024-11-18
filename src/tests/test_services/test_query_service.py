import pytest
from src.services.query_service import QueryService
import logging

logger = logging.getLogger(__name__)


class TestSearchOperations:
    """Test search operations following notebook patterns"""

    def test_semantic_search(self, test_services):
        """Test semantic search capabilities"""
        _, query_service = test_services
        results = query_service.search(
            "machine learning", query_type="semantic", limit=1
        )

        assert len(results) == 1
        assert "machine learning" in results[0]["text"].lower()
        assert isinstance(results[0]["score"], float)
        assert isinstance(results[0]["metadata"], dict)

    def test_sql_search(self, test_services):
        """Test SQL search with metadata"""
        _, query_service = test_services
        # SQL query needs exact metadata match
        results = query_service.search(
            'SELECT * FROM txtai WHERE metadata LIKE \'{"category":"tech"}\'',
            query_type="sql",
        )

        assert len(results) == 1
        assert results[0]["metadata"]["category"] == "tech"
        assert isinstance(results[0]["score"], float)

    def test_hybrid_search(self, test_services):
        """Test hybrid search combining semantic and keyword"""
        _, query_service = test_services
        results = query_service.search("machine learning", query_type="hybrid", limit=1)

        assert len(results) == 1
        assert isinstance(results[0]["score"], float)
        assert isinstance(results[0]["metadata"], dict)


class TestResultHandling:
    """Test result processing and formatting"""

    def test_result_format(self, test_services):
        """Test search result format matches notebook pattern"""
        _, query_service = test_services
        results = query_service.search("machine learning", limit=1)
        result = results[0]

        # Verify structure from notebook pattern
        assert all(key in result for key in ["id", "text", "score", "metadata"])
        assert isinstance(result["score"], float)
        assert isinstance(result["metadata"], dict)

    def test_metadata_parsing(self, test_services):
        """Test metadata handling matches notebook format"""
        _, query_service = test_services
        results = query_service.search("machine learning", limit=1)
        metadata = results[0]["metadata"]

        # Check metadata structure from notebook
        assert isinstance(metadata, dict)
        assert "category" in metadata
        assert metadata["category"] == "tech"
        assert isinstance(metadata["tags"], list)

    def test_document_indexing(self, test_services):
        """Verify documents are indexed with metadata"""
        embeddings_service, _ = test_services

        # Search directly with embeddings to see raw results
        results = embeddings_service.embeddings.search("machine learning", 1)
        result = results[0]

        # Debug what we got
        logger.info(f"Raw search result: {result}")

        # Check if we can find the document by metadata
        sql_results = embeddings_service.embeddings.search(
            'SELECT * FROM txtai WHERE metadata LIKE \'%"category":"tech"%\''
        )
        assert len(sql_results) > 0, "Should find documents with tech category"

        # Verify metadata in semantic results
        semantic_results = embeddings_service.embeddings.search("machine learning", 1)
        assert semantic_results[0].get(
            "metadata"
        ), "Semantic results should include metadata"
