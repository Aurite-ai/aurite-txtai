import pytest
import logging
from src.services import registry
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestServiceIntegration:
    """Test service initialization and basic integration"""

    @pytest.mark.first
    async def test_service_initialization(self, initialized_services):
        """Test that all services initialize properly"""
        logger.info("\n=== Testing Service Initialization ===")

        # Get initialized services
        services = await initialized_services

        # Verify services in dependency order
        assert services.config_service._initialized, "Config service not initialized"
        assert services.embeddings_service._initialized, "Embeddings service not initialized"
        assert services.llm_service._initialized, "LLM service not initialized"
        assert services.rag_service._initialized, "RAG service not initialized"
        assert services.txtai_service._initialized, "TxtAI service not initialized"

        logger.info("All services initialized successfully")

    @pytest.mark.second
    async def test_basic_search(self, setup_test_data):
        """Test basic search functionality"""
        logger.info("\n=== Testing Basic Search ===")

        query = "machine learning"
        results = await registry.embeddings_service.hybrid_search(query, limit=1)

        assert len(results) > 0
        assert "score" in results[0]
        assert "text" in results[0]
        assert "machine learning" in results[0]["text"].lower()

        logger.info(f"Search successful: {results[0]['text'][:50]}...")

    @pytest.mark.third
    async def test_basic_rag(self, setup_test_data):
        """Test basic RAG functionality"""
        logger.info("\n=== Testing Basic RAG ===")

        query = "What is machine learning?"
        response = await registry.rag_service.generate(query)

        assert isinstance(response, dict)
        assert "query" in response
        assert "context" in response
        assert "response" in response
        assert len(response["context"]) > 0

        logger.info(f"RAG response: {response['response'][:100]}...")

    @pytest.mark.fourth
    async def test_message_flow(self, setup_test_data):
        """Test message handling through txtai service"""
        logger.info("\n=== Testing Message Flow ===")

        message = Message(
            type=MessageType.RAG_REQUEST,
            data={"query": "What is artificial intelligence?"},
            session_id="test-session",
        )

        response = await registry.txtai_service.handle_request(message)

        assert response is not None
        assert "query" in response
        assert "context" in response
        assert "response" in response

        logger.info(f"Message flow successful: {response['response'][:100]}...")
