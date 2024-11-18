import pytest
import json
import logging

from src.services.query_service import QueryService

logger = logging.getLogger(__name__)


class TestQueryService:
    """Test query service functionality"""

    def test_semantic_search(self, test_services):
        """Test semantic search functionality"""
        _, query_service = test_services

        # Perform semantic search
        results = query_service.semantic_search("machine learning", limit=2)

        # Verify results structure
        assert len(results) > 0
        first_result = results[0]
        assert all(k in first_result for k in ["id", "text", "score", "metadata"])

        # Verify scoring
        assert first_result["score"] > 0
        assert "machine learning" in first_result["text"].lower()

        # Verify metadata
        assert first_result["metadata"]["category"] == "tech"
        assert isinstance(first_result["metadata"]["tags"], list)

    def test_sql_search(self, test_services):
        """Test SQL search functionality"""
        _, query_service = test_services

        # Basic SQL query
        sql_query = '''
            SELECT id, text, tags
            FROM txtai
            WHERE tags LIKE '%"category": "tech"%'
        '''
        results = query_service.sql_search(sql_query)

        # Verify results
        assert len(results) > 0
        first_result = results[0]
        assert all(k in first_result for k in ["id", "text", "metadata"])

        # Verify metadata
        assert first_result["metadata"]["category"] == "tech"
        assert isinstance(first_result["metadata"]["tags"], list)

    def test_sql_search_complex(self, test_services):
        """Test complex SQL queries with multiple conditions"""
        _, query_service = test_services

        # Complex SQL query with multiple conditions
        sql_query = '''
            SELECT id, text, tags
            FROM txtai
            WHERE tags LIKE '%"category": "tech"%'
            AND tags LIKE '%"priority": 1%'
        '''
        results = query_service.sql_search(sql_query)

        # Verify filtered results
        assert len(results) == 1
        assert results[0]["metadata"]["category"] == "tech"
        assert results[0]["metadata"]["priority"] == 1

    def test_semantic_search_ranking(self, test_services):
        """Test semantic search result ranking"""
        _, query_service = test_services

        # Search with specific term
        results = query_service.semantic_search("machine learning")

        # Verify score ordering
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

        # Check best match
        best_match = results[0]
        assert "machine learning" in best_match["text"].lower()
        assert best_match["score"] > 0.5

    def test_hybrid_search(self, test_services):
        """Test hybrid search functionality"""
        _, query_service = test_services

        # Perform hybrid search
        results = query_service.hybrid_search("machine learning", limit=2)

        # Verify results structure
        assert len(results) > 0
        first_result = results[0]
        assert all(k in first_result for k in ["id", "text", "score", "metadata"])

        # Verify scoring
        assert first_result["score"] > 0
        assert "machine learning" in first_result["text"].lower()

        # Verify metadata
        assert first_result["metadata"]["category"] == "tech"
        assert isinstance(first_result["metadata"]["tags"], list)

    def test_hybrid_search_ranking(self, test_services):
        """Test hybrid search result ranking"""
        _, query_service = test_services

        # Search with specific term
        results = query_service.hybrid_search("machine learning")

        # Verify score ordering
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

        # Check best match combines semantic and term matching
        best_match = results[0]
        assert "machine learning" in best_match["text"].lower()
        assert best_match["score"] > 0.5

    def test_hybrid_search_empty_results(self, test_services):
        """Test hybrid search with irrelevant query"""
        _, query_service = test_services

        # Search for irrelevant term
        results = query_service.hybrid_search("nonexistent term xyz")

        # Should return results but with very low scores
        assert all(
            result["score"] < 0.1 for result in results
        ), "Irrelevant query should have very low scores"

    def test_hybrid_search_weights(self, test_services):
        """Test hybrid search differs from pure semantic search"""
        _, query_service = test_services

        # Test with exact phrase vs individual terms
        phrase_results = query_service.hybrid_search('"machine learning"', limit=1)
        term_results = query_service.hybrid_search('machine learning', limit=1)

        # Exact phrase match should score differently than term match
        assert (
            phrase_results[0]["score"] != term_results[0]["score"]
        ), "Hybrid search should weight exact matches differently"
