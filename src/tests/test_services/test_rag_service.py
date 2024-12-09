from __future__ import annotations

import logging

import pytest

from src.services import registry


logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestRAGService:
    """Test RAG service functionality"""

    async def test_service_initialization(self, initialized_services) -> None:
        """Test that RAG service initializes correctly"""
        assert registry.rag_service.initialized
        assert registry.embeddings_service.initialized
        assert registry.llm_service.initialized
        logger.info("RAG service and dependencies initialized successfully")

    async def test_basic_generation(self, initialized_services, setup_test_data) -> None:
        """Test basic RAG generation"""
        query = "What is machine learning?"
        logger.info("\n=== Testing RAG generation ===")
        logger.info(f"Query: {query}")

        response = await registry.rag_service.generate(query)
        assert isinstance(response, str)
        assert len(response) > 0

    async def test_no_context_handling(self, initialized_services) -> None:
        """Test RAG handling when no relevant context found"""
        response = await registry.rag_service.generate("What is quantum physics?")
        assert isinstance(response, str)
        assert len(response) > 0

    async def test_error_handling(self, initialized_services) -> None:
        """Test RAG error handling"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await registry.rag_service.generate("")

    async def test_context_search(self, initialized_services, setup_test_data) -> None:
        """Test context search functionality"""
        query = "machine learning"
        logger.info(f"\nTesting context search with query: {query}")

        results = await registry.rag_service.search_context(query, limit=2)
        assert len(results) > 0
        assert all("score" in r for r in results)
        assert all("text" in r for r in results)

    async def test_min_score_filtering(self, initialized_services, setup_test_data) -> None:
        """Test minimum score filtering in context search"""
        results = await registry.rag_service.search_context(
            "machine learning", limit=2, min_score=0.99
        )
        assert len(results) == 0  # No results should pass this high threshold

    async def test_context_relevance(self, initialized_services, setup_test_data) -> None:
        """Test that context results are relevant to query"""
        query = "artificial intelligence"
        logger.info(f"\nTesting context relevance with query: {query}")

        results = await registry.rag_service.search_context(query, limit=3)
        assert len(results) > 0
        assert any(query.lower() in r["text"].lower() or "ai" in r["text"].lower() for r in results)
