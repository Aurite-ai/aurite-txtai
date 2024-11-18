import pytest
import logging
from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class TestLLMService:
    """Test LLM service functionality"""

    def test_basic_generation(self):
        """Test basic text generation"""
        service = LLMService()

        response = service.generate("What is 2+2?")
        assert isinstance(response, str)
        assert len(response) > 0
        assert "4" in response.lower()

    def test_context_generation(self):
        """Test generation with context"""
        service = LLMService()

        context = "The capital of France is Paris."
        question = "What is the capital of France?"

        response = service.generate_with_context(question, context)
        assert isinstance(response, str)
        assert len(response) > 0
        assert "paris" in response.lower()

    def test_message_format(self):
        """Test different message formats"""
        service = LLMService()

        # Test string format
        str_response = service.generate("Hello")
        assert isinstance(str_response, str)

        # Test message list format
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "Hello"},
        ]
        list_response = service.generate(messages)
        assert isinstance(list_response, str)

    def test_error_handling(self):
        """Test error handling in generation"""
        service = LLMService()

        # Test with invalid message format
        invalid_messages = [{"invalid": "format"}]
        response = service.generate(invalid_messages)
        assert "error" in response.lower()

    def test_context_constraints(self):
        """Test that context-based generation stays within context"""
        service = LLMService()

        context = "The sky is blue."
        question = "What color is grass?"

        response = service.generate_with_context(question, context)
        assert isinstance(response, str)
        assert "cannot" in response.lower() or "not" in response.lower()
