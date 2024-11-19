import pytest
from src.services.rag_service import RAGService, rag_service
from src.services.embeddings_service import embeddings_service


class TestRAGService:
    """Test RAG service functionality"""

    @pytest.fixture(autouse=True)
    async def setup_test_data(self, setup_services):
        """Setup test data before each test"""
        # Initialize RAG service
        self.service = rag_service
        await self.service.initialize()

        # Add test documents using embeddings service
        test_docs = [
            {
                "id": "doc1",
                "text": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience.",
                "metadata": {
                    "category": "tech",
                    "tags": ["ML", "AI"],
                },
            },
            {
                "id": "doc2",
                "text": "Natural language processing (NLP) is a branch of AI that helps computers understand human language.",
                "metadata": {
                    "category": "tech",
                    "tags": ["NLP", "AI"],
                },
            },
        ]
        # Use embeddings service to add documents
        await embeddings_service.add(test_docs)

        # Return self.service to ensure it's available
        return self.service

    @pytest.mark.asyncio
    async def test_basic_generation(self, setup_test_data):
        """Test basic RAG generation"""
        response = await self.service.generate("What is machine learning?")
        assert isinstance(response, dict)
        assert "query" in response
        assert "context" in response
        assert "response" in response
        assert len(response["context"]) > 0  # Should find relevant context

    @pytest.mark.asyncio
    async def test_no_context_handling(self, setup_test_data):
        """Test RAG handling when no relevant context found"""
        response = await self.service.generate("What is quantum physics?")
        assert isinstance(response, dict)
        assert "query" in response
        assert isinstance(response["context"], list)
        assert len(response["context"]) == 0  # Should have no relevant context

    @pytest.mark.asyncio
    async def test_error_handling(self, setup_test_data):
        """Test RAG error handling"""
        with pytest.raises(ValueError):
            await self.service.generate("")  # Empty query should raise error

    @pytest.mark.asyncio
    async def test_context_search(self, setup_test_data):
        """Test context search functionality"""
        results = await self.service.search_context("machine learning", limit=2)
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, dict) for r in results)
        assert all("score" in r for r in results)
        assert all("text" in r for r in results)
        assert all("metadata" in r for r in results)

    @pytest.mark.asyncio
    async def test_min_score_filtering(self, setup_test_data):
        """Test minimum score filtering in context search"""
        # Set very high min_score to test filtering
        results = await self.service.search_context("machine learning", limit=2, min_score=0.99)
        assert isinstance(results, list)
        assert len(results) == 0  # Should filter out all results
