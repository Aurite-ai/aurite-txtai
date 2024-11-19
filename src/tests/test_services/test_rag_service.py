import pytest
import logging
from src.services import registry

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestRAGService:
    """Test RAG service functionality"""

    async def test_service_initialization(self, initialized_services):
        """Test that RAG service initializes correctly"""
        # Wait for services to initialize
        await initialized_services

        # Verify RAG service and its dependencies
        assert registry.rag_service.initialized
        assert registry.embeddings_service.initialized
        assert registry.llm_service.initialized
        logger.info("RAG service and dependencies initialized successfully")

    async def test_basic_generation(self, setup_test_data):
        """Test basic RAG generation"""
        async for _ in setup_test_data:
            query = "What is machine learning?"
            logger.info(f"\n=== Testing RAG generation ===")
            logger.info(f"Query: {query}")

            response = await registry.rag_service.generate(query)
            assert isinstance(response, str)
            assert len(response) > 0
            break

    async def test_no_context_handling(self):
        """Test RAG handling when no relevant context found"""
        response = await registry.rag_service.generate("What is quantum physics?")
        assert "No relevant context found" in response

    async def test_error_handling(self):
        """Test RAG error handling"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await registry.rag_service.generate("")

    async def test_context_search(self, setup_test_data):
        """Test context search functionality"""
        async for _ in setup_test_data:
            query = "machine learning"
            logger.info(f"\nTesting context search with query: {query}")

            results = await registry.rag_service.search_context(query, limit=2)
            assert len(results) > 0
            assert all("score" in r for r in results)
            assert all("text" in r for r in results)
            break

    async def test_min_score_filtering(self, setup_test_data):
        """Test minimum score filtering in context search"""
        async for _ in setup_test_data:
            results = await registry.rag_service.search_context(
                "machine learning", limit=2, min_score=0.99
            )
            assert len(results) == 0  # No results should pass this high threshold
            break

    async def test_context_relevance(self, setup_test_data):
        """Test that context results are relevant to query"""
        async for _ in setup_test_data:
            query = "artificial intelligence"
            logger.info(f"\nTesting context relevance with query: {query}")

            results = await registry.rag_service.search_context(query, limit=3)
            assert len(results) > 0
            assert any(
                query.lower() in r["text"].lower() or "ai" in r["text"].lower() for r in results
            )
            break
