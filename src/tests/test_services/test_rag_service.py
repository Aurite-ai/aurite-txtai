import pytest
import logging
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class TestRAGService:
    """Test RAG service functionality"""

    def test_basic_generation(self):
        """Test basic RAG generation"""
        service = RAGService()

        question = "What is machine learning?"
        response = service.generate(question)

        assert isinstance(response, str)
        assert len(response) > 0
        assert "machine learning" in response.lower()

    def test_no_context_handling(self):
        """Test handling when no relevant context is found"""
        service = RAGService()

        # Use a very specific question unlikely to have context
        question = "What is the exact temperature in my room right now?"
        response = service.generate(question)

        assert isinstance(response, str)
        assert len(response) > 0
        assert any(
            phrase in response.lower() for phrase in ["cannot", "don't have", "no information"]
        )

    def test_batch_generation(self):
        """Test batch RAG generation"""
        service = RAGService()

        questions = ["What is deep learning?", "How does NLP work?"]

        responses = service.batch_generate(questions)

        assert isinstance(responses, list)
        assert len(responses) == len(questions)
        assert all(isinstance(r, str) for r in responses)
        assert all(len(r) > 0 for r in responses)

    def test_custom_template(self):
        """Test RAG with custom template"""
        service = RAGService()

        template = """<|im_start|>system
You are a technical expert.<|im_end|>
<|im_start|>user
Context: {context}
Technical explanation of: {question}<|im_end|>
<|im_start|>assistant"""

        response = service.generate("What are neural networks?", template=template)

        assert isinstance(response, str)
        assert len(response) > 0
        assert "neural" in response.lower()

    def test_error_handling(self):
        """Test error handling in RAG service"""
        service = RAGService()

        # Test with invalid input
        with pytest.raises(Exception):
            service.generate(None)

        with pytest.raises(Exception):
            service.batch_generate(None)
