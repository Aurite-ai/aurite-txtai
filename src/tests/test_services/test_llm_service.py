import pytest
import logging
from src.services import registry

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestLLMService:
    """Test LLM service functionality"""

    async def test_basic_generation(self, initialized_services):
        """Test basic text generation"""
        # No need to await initialized_services
        prompt = "What is 2+2?"
        response = await registry.llm_service.generate(prompt)
        assert isinstance(response, str)
        assert len(response) > 0
        assert "4" in response.lower()
        logger.info(f"Generated response: {response[:100]}...")

    async def test_context_generation(self):
        """Test generation with context"""
        context = "The capital of France is Paris. It is known for the Eiffel Tower."
        question = "What is the capital of France?"

        response = await registry.llm_service.generate_with_context(question, context)

        assert isinstance(response, str)
        assert len(response) > 0
        assert "paris" in response.lower()
        logger.info(f"Context-based response: {response[:100]}...")

    async def test_message_format(self):
        """Test different message formats"""
        # Test string format
        str_response = await registry.llm_service.generate("Hello")
        assert isinstance(str_response, str)
        logger.info(f"String format response: {str_response[:100]}...")

        # Test message list format
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "Hello"},
        ]
        list_response = await registry.llm_service.generate(messages)
        assert isinstance(list_response, str)
        logger.info(f"Message list format response: {list_response[:100]}...")

    async def test_error_handling(self):
        """Test error handling in generation"""
        # Test with empty prompt
        empty_response = await registry.llm_service.generate("")
        assert isinstance(empty_response, str)
        assert "error" in empty_response.lower() or len(empty_response) == 0

        # Test with invalid message format
        invalid_messages = [{"invalid": "format"}]
        error_response = await registry.llm_service.generate(invalid_messages)
        assert isinstance(error_response, str)
        assert "error" in error_response.lower()

        logger.info(f"Error handling response: {error_response[:100]}...")

    async def test_context_constraints(self):
        """Test that context-based generation stays within context"""
        context = "The sky is blue. Birds can fly in the sky."
        question = "What color is grass?"

        response = await registry.llm_service.generate_with_context(question, context)

        assert isinstance(response, str)
        assert len(response) > 0
        # Should indicate it can't answer about grass color from the given context
        assert any(word in response.lower() for word in ["cannot", "not", "unavailable", "context"])
        logger.info(f"Context constraint response: {response[:100]}...")

    async def test_system_prompts(self, test_settings):
        """Test system prompt handling"""
        # Test default system prompt
        response = await registry.llm_service.generate("Hello")
        assert isinstance(response, str)
        logger.info(f"Default prompt response: {response[:100]}...")

        # Test RAG system prompt
        context = "AI helps automate tasks."
        question = "How does AI help?"
        rag_response = await registry.llm_service.generate_with_context(question, context)
        assert isinstance(rag_response, str)
        logger.info(f"RAG prompt response: {rag_response[:100]}...")
