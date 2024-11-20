import pytest
import logging
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestServiceInitialization:
    """Test service initialization and basic functionality"""

    async def test_core_services_initialized(self, initialized_services):
        """Test that core services are properly initialized"""
        assert initialized_services["embeddings"].initialized
        assert initialized_services["llm"].initialized
        assert initialized_services["rag"].initialized
        logger.info("Core services initialized successfully")

    async def test_redis_services_initialized(self, initialized_services):
        """Test that Redis services are properly initialized"""
        assert initialized_services["communication"].initialized
        assert initialized_services["txtai"].initialized
        assert initialized_services["stream"].initialized
        logger.info("Redis services initialized successfully")

    async def test_embeddings_functionality(self, initialized_services, setup_test_data):
        """Test basic embeddings functionality"""
        embeddings_service = initialized_services["embeddings"]
        results = await embeddings_service.search("machine learning")
        assert len(results) > 0
        assert isinstance(results[0]["score"], float)
        logger.info(f"Search returned {len(results)} results")

    async def test_llm_functionality(self, initialized_services):
        """Test basic LLM functionality"""
        llm_service = initialized_services["llm"]
        response = await llm_service.generate("Say hello!")
        assert isinstance(response, str)
        assert len(response) > 0
        logger.info("LLM generation successful")

    async def test_rag_functionality(self, initialized_services, setup_test_data):
        """Test basic RAG functionality"""
        rag_service = initialized_services["rag"]
        response = await rag_service.generate("What is machine learning?")
        assert isinstance(response, str)
        assert len(response) > 0
        logger.info("RAG generation successful")

    async def test_message_handling(self, initialized_services, setup_test_data):
        """Test message handling through txtai service"""
        txtai_service = initialized_services["txtai"]

        # Test RAG request
        message = Message(
            type=MessageType.RAG_REQUEST, data={"query": "What is AI?"}, session_id="test-session"
        )

        response = await txtai_service.handle_request(message)
        assert response["session_id"] == "test-session"
        assert "answer" in response
        logger.info("Message handling successful")
