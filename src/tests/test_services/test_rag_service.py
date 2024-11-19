import pytest
import logging
from src.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class TestRAGService:
    """Test RAG service functionality"""

    @pytest.mark.asyncio
    async def test_basic_generation(self, setup_test_data):
        """Test basic RAG generation"""
        query = "What is machine learning?"
        logger.info(f"\n=== Testing RAG generation ===")
        logger.info(f"Query: {query}")

        response = await rag_service.generate(query)
        logger.info(f"RAG response: {response}")

        assert isinstance(response, dict)
        assert "query" in response
        assert "context" in response
        assert "response" in response
        assert len(response["context"]) > 0, f"No context found for query: {query}"
        assert any("machine learning" in doc["text"].lower() for doc in response["context"])

    @pytest.mark.asyncio
    async def test_no_context_handling(self, setup_test_data):
        """Test RAG handling when no relevant context found"""
        response = await rag_service.generate("What is quantum physics?")
        assert isinstance(response, dict)
        assert "query" in response
        assert isinstance(response["context"], list)
        assert len(response["context"]) == 0  # Should have no context

    @pytest.mark.asyncio
    async def test_error_handling(self, setup_test_data):
        """Test RAG error handling"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await rag_service.generate("")

    @pytest.mark.asyncio
    async def test_context_search(self, setup_test_data):
        """Test context search functionality"""
        query = "machine learning"
        logger.info(f"\nTesting context search with query: {query}")

        results = await rag_service.search_context(query, limit=2)
        logger.info(f"Search results: {results}")

        assert isinstance(results, list)
        assert len(results) > 0, f"No results found for query: {query}"
        for result in results:
            assert isinstance(result, dict)
            assert "score" in result
            assert "text" in result
            assert "metadata" in result
            logger.info(f"Result score: {result['score']}, text: {result['text'][:50]}...")

    @pytest.mark.asyncio
    async def test_min_score_filtering(self, setup_test_data):
        """Test minimum score filtering in context search"""
        # Set impossibly high min_score to test filtering
        results = await rag_service.search_context("machine learning", limit=2, min_score=0.99)
        assert isinstance(results, list)
        assert len(results) == 0  # Should filter out all results

    @pytest.mark.asyncio
    async def test_context_relevance(self, setup_test_data):
        """Test that context results are relevant to query"""
        query = "artificial intelligence"
        logger.info(f"\nTesting context relevance with query: {query}")

        results = await rag_service.search_context(query, limit=3)
        logger.info(f"Relevance search results: {results}")

        # Verify we get relevant results
        assert len(results) > 0, f"No results found for query: {query}"
        # Check that results contain relevant terms
        relevant_terms = ["ai", "artificial intelligence", "machine learning", "nlp"]
        for result in results:
            text = result["text"].lower()
            assert any(term in text for term in relevant_terms)
            assert 0 <= result["score"] <= 1
            logger.info(f"Result score: {result['score']}, text: {result['text'][:50]}...")
