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

    async def test_basic_rag(self, initialized_services, setup_test_data) -> None:
        """Test basic RAG functionality"""
        query = "What is machine learning?"
        logger.info("\n=== Testing RAG answer generation ===")
        logger.info(f"Query: {query}")

        result = await registry.rag_service.answer(query)
        assert isinstance(result, dict)
        assert "question" in result
        assert "context" in result
        assert "answer" in result
        assert result["question"] == query
        assert len(result["answer"]) > 0
        assert "machine learning" in result["context"].lower()

    async def test_no_context_handling(self, initialized_services) -> None:
        """Test RAG handling when no relevant context found"""
        query = "What is quantum physics?"
        result = await registry.rag_service.answer(query)
        assert isinstance(result, dict)
        assert result["question"] == query
        assert "No relevant context found" in result["context"]
        assert len(result["answer"]) > 0

    async def test_error_handling(self, initialized_services) -> None:
        """Test RAG error handling"""
        # Test empty query
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await registry.rag_service.answer("")

        # Test uninitialized service
        from src.services.core.rag_service import RAGService

        test_service = RAGService()
        with pytest.raises(RuntimeError, match=".*not initialized"):
            await test_service.answer("test")

    async def test_context_search(self, initialized_services, setup_test_data) -> None:
        """Test context search functionality"""
        query = "machine learning"
        logger.info(f"\nTesting RAG with query: {query}")

        # Test with different limits
        result1 = await registry.rag_service.answer(query, limit=1)
        result2 = await registry.rag_service.answer(query, limit=2)

        # Count context documents
        doc_count1 = result1["context"].count("Document ")
        doc_count2 = result2["context"].count("Document ")

        assert doc_count1 == 1
        assert doc_count2 == 2

    async def test_temperature_control(self, initialized_services, setup_test_data) -> None:
        """Test temperature parameter in answer generation"""
        query = "What is artificial intelligence?"

        # Generate answers with different temperatures
        result1 = await registry.rag_service.answer(query, temperature=0.1)
        result2 = await registry.rag_service.answer(query, temperature=0.9)

        assert result1["answer"] != result2["answer"]
        assert "artificial intelligence" in result1["context"].lower()
        assert "artificial intelligence" in result2["context"].lower()

    async def test_min_score_filtering(self, initialized_services, setup_test_data) -> None:
        """Test minimum score filtering in context retrieval"""
        query = "machine learning"

        # Test with high min_score
        result = await registry.rag_service.answer(query, min_score=0.99)
        assert "No relevant context found" in result["context"]

        # Test with normal min_score
        result = await registry.rag_service.answer(query, min_score=0.0)
        assert "No relevant context found" not in result["context"]
        assert "machine learning" in result["context"].lower()

    async def test_context_relevance(self, initialized_services, setup_test_data) -> None:
        """Test that context results are relevant to query"""
        query = "artificial intelligence and machine learning"
        logger.info(f"\nTesting context relevance with query: {query}")

        result = await registry.rag_service.answer(query)
        assert "artificial intelligence" in result["context"].lower()
        assert "machine learning" in result["context"].lower()
        assert len(result["answer"]) > 0
