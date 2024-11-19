import pytest
import logging
from src.services import registry
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestServiceIntegration:
    """Test service integration"""

    async def test_service_initialization(self, initialized_services):
        """Test that all services initialize correctly"""
        logger.info("\n=== Testing Service Initialization ===")

        # Get initialized services
        services = await initialized_services

        # Verify all services are initialized
        assert services.config_service.initialized
        assert services.embeddings_service.initialized
        assert services.llm_service.initialized
        assert services.rag_service.initialized
        assert services.txtai_service.initialized

        logger.info("All services initialized successfully")

    async def test_basic_search(self, initialized_services, setup_test_data):
        """Test basic search functionality"""
        logger.info("\n=== Testing Basic Search ===")

        # Wait for test data setup
        async for _ in setup_test_data:
            # Search for documents
            results = await registry.embeddings_service.search("machine learning", limit=1)
            assert len(results) == 1
            assert "machine learning" in results[0]["text"].lower()
            break

    async def test_basic_rag(self, initialized_services, setup_test_data):
        """Test basic RAG functionality"""
        logger.info("\n=== Testing Basic RAG ===")

        # Wait for test data setup
        async for _ in setup_test_data:
            # Perform RAG query
            context = await registry.rag_service.get_context("What is artificial intelligence?")
            assert len(context) > 0

            # Generate response with context
            response = await registry.llm_service.generate_with_context(
                "What is artificial intelligence?", context
            )
            assert isinstance(response, str)
            assert len(response) > 0
            break

    async def test_message_flow(self, initialized_services, setup_test_data):
        """Test message flow through services"""
        logger.info("\n=== Testing Message Flow ===")

        # Wait for test data setup
        async for _ in setup_test_data:
            # Test RAG message flow
            rag_request = Message(
                type=MessageType.RAG_REQUEST,
                data={"query": "What is artificial intelligence?"},
                session_id="test-session",
            )

            # Get context
            context = await registry.rag_service.get_context(rag_request.data["query"])
            assert len(context) > 0

            # Generate response
            response = await registry.llm_service.generate_with_context(
                rag_request.data["query"], context
            )
            assert isinstance(response, str)
            assert len(response) > 0

            # Create response message
            rag_response = Message(
                type=MessageType.RAG_RESPONSE,
                data={"response": response, "context": context},
                session_id=rag_request.session_id,
            )

            assert rag_response.type == MessageType.RAG_RESPONSE
            assert isinstance(rag_response.data["response"], str)
            assert len(rag_response.data["response"]) > 0
            break
