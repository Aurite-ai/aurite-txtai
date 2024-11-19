import pytest
import json
import logging
from src.services.query_service import QueryService
from src.services.embeddings_service import embeddings_service

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestQueryService:
    """Test query service functionality"""

    async def test_query_types(self, setup_test_data):
        """Test different query types"""
        query_service = QueryService(embeddings_service.embeddings)

        # Test semantic search
        semantic_results = await query_service.semantic_search("machine learning", limit=1)
        assert len(semantic_results) > 0
        assert "score" in semantic_results[0]
        assert "text" in semantic_results[0]

        # Test SQL search
        sql_query = """
            SELECT id, text, tags
            FROM txtai
            WHERE tags LIKE '%"category": "tech"%'
        """
        sql_results = await query_service.sql_search(sql_query)
        assert len(sql_results) > 0
        assert "id" in sql_results[0]
        assert "text" in sql_results[0]

        # Test hybrid search
        hybrid_results = await query_service.hybrid_search("machine learning", limit=1)
        assert len(hybrid_results) > 0
        assert "score" in hybrid_results[0]
        assert "text" in hybrid_results[0]
