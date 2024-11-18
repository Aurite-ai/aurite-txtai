import pytest
from src.services.rag_service import RAGService
from src.services.embeddings_service import embeddings_service


class TestRAGService:
    """Test RAG service functionality"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Setup test data before each test"""
        self.service = RAGService()

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
        embeddings_service.add(test_docs)

    def test_basic_generation(self):
        """Test basic RAG generation"""
        response = self.service.generate("What is machine learning?")
        assert isinstance(response, dict)
        assert "answer" in response
        assert "context" in response
        assert "citations" in response
        assert len(response["context"]) > 0  # Should find relevant context

    def test_no_context_handling(self):
        """Test RAG handling when no relevant context found"""
        response = self.service.generate("What is quantum physics?")
        assert isinstance(response, dict)
        assert "answer" in response
        assert isinstance(response["context"], list)
        assert len(response["context"]) == 0  # Should have no relevant context

    def test_error_handling(self):
        """Test RAG error handling"""
        with pytest.raises(Exception):
            self.service.generate("")  # Empty query should raise error

    # Removed batch_generation and custom_template tests since they're not supported
