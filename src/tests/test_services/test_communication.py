import pytest
import logging
from src.services import registry
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestCommunicationService:
    """Test communication service functionality"""

    async def test_service_initialization(self, initialized_services):
        """Test that communication service initializes correctly"""
        assert registry.communication_service.initialized
        assert registry.stream_service.initialized
        logger.info("Communication service and dependencies initialized successfully")

    async def test_handle_rag_request(self, initialized_services, setup_test_data):
        """Test handling RAG request messages"""
        # Create test message
        message = Message(
            type=MessageType.RAG_REQUEST,
            data={"query": "What is machine learning?"},
            session_id="test-session",
        )

        # Process message
        responses = []
        async for response in registry.communication_service.handle_message(message):
            responses.append(response)

        # Verify responses
        assert len(responses) == 2  # Context and response messages
        assert responses[0].type == MessageType.RAG_CONTEXT
        assert responses[1].type == MessageType.RAG_RESPONSE

    async def test_handle_unsupported_message(self):
        """Test handling unsupported message types"""
        message = Message(
            type=MessageType.LLM_REQUEST,  # Unsupported type
            data={"prompt": "test"},
            session_id="test-session",
        )

        responses = []
        async for response in registry.communication_service.handle_message(message):
            responses.append(response)

        assert len(responses) == 1
        assert responses[0].type == MessageType.ERROR
        assert "Unsupported message type" in responses[0].data["error"]

    async def test_error_handling(self):
        """Test error handling in message processing"""
        message = Message(
            type=MessageType.RAG_REQUEST,
            data={},  # Missing query
            session_id="test-session",
        )

        responses = []
        async for response in registry.communication_service.handle_message(message):
            responses.append(response)

        assert len(responses) == 1
        assert responses[0].type == MessageType.ERROR
        assert "Query not found" in responses[0].data["error"]

    async def test_session_handling(self, setup_test_data):
        """Test handling messages for different sessions"""
        await setup_test_data

        # Create messages for different sessions
        session1_msg = Message(
            type=MessageType.RAG_REQUEST,
            data={"query": "What is AI?"},
            session_id="session1",
        )
        session2_msg = Message(
            type=MessageType.RAG_REQUEST,
            data={"query": "What is ML?"},
            session_id="session2",
        )

        # Process messages
        responses1 = []
        responses2 = []
        async for response in registry.communication_service.handle_message(session1_msg):
            responses1.append(response)
        async for response in registry.communication_service.handle_message(session2_msg):
            responses2.append(response)

        # Verify session isolation
        assert all(r.session_id == "session1" for r in responses1)
        assert all(r.session_id == "session2" for r in responses2)
