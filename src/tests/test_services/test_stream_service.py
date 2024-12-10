from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.models.messages import Message, MessageType
from src.services.redis.communication_service import CommunicationService
from src.services.redis.stream_service import StreamService
from src.services.redis.txtai_service import TxtAIService


@pytest.fixture
def mock_comm_service():
    """Mock communication service"""
    service = AsyncMock(spec=CommunicationService)
    service.read_stream = AsyncMock(return_value=[])
    service.publish_to_stream = AsyncMock()
    return service


@pytest.fixture
def mock_txtai_service():
    """Mock txtai service"""
    service = AsyncMock(spec=TxtAIService)
    service.handle_request = AsyncMock()
    return service


@pytest.fixture
async def test_stream_service(test_settings, mock_comm_service, mock_txtai_service):
    """Create test stream service instance"""
    service = StreamService()
    await service.initialize(test_settings, mock_comm_service, mock_txtai_service)
    yield service
    await service.stop()


class TestStreamService:
    """Test stream service functionality"""

    async def test_initialization(self, test_settings, mock_comm_service, mock_txtai_service) -> None:
        """Test stream service initialization"""
        service = StreamService()
        assert not service._initialized

        await service.initialize(test_settings, mock_comm_service, mock_txtai_service)
        assert service._initialized
        assert service.comm_service == mock_comm_service
        assert service.txtai_service == mock_txtai_service

    async def test_initialization_failure(self, test_settings) -> None:
        """Test initialization failure without required services"""
        service = StreamService()
        with pytest.raises(RuntimeError):
            await service.start()

    async def test_start_stop(self, test_stream_service) -> None:
        """Test start and stop functionality"""
        assert not test_stream_service._running
        await test_stream_service.start()
        assert test_stream_service._running
        assert test_stream_service._task is not None

        await test_stream_service.stop()
        assert not test_stream_service._running
        assert test_stream_service._task is None

    async def test_multiple_start_stop(self, test_stream_service) -> None:
        """Test multiple start/stop cycles"""
        for _ in range(3):
            await test_stream_service.start()
            assert test_stream_service._running
            await test_stream_service.stop()
            assert not test_stream_service._running

    async def test_message_processing(self, test_stream_service, mock_comm_service, mock_txtai_service) -> None:
        """Test message processing"""
        # Setup test message
        test_message = {
            "data": {
                "type": MessageType.RAG_REQUEST.value,
                "data": {"query": "test query"},
                "session_id": "test-session",
            }
        }

        # Configure mock to return message only for rag_stream
        async def mock_read_stream(stream: str):
            if stream == "rag_stream":
                return [test_message]
            return []

        mock_comm_service.read_stream.side_effect = mock_read_stream

        # Setup response
        response_message = Message(
            type=MessageType.RAG_RESPONSE, data={"answer": "test answer"}, session_id="test-session"
        )
        mock_txtai_service.handle_request.return_value = response_message.to_dict()

        # Start service and let it process one message
        await test_stream_service.start()
        await asyncio.sleep(0.1)  # Allow time for processing
        await test_stream_service.stop()

        # Verify message handling
        mock_txtai_service.handle_request.assert_called_once()
        mock_comm_service.publish_to_stream.assert_called_once()

    async def test_invalid_message_handling(self, test_stream_service, mock_comm_service) -> None:
        """Test handling of invalid messages"""
        # Setup invalid message
        invalid_message = {"data": "invalid"}
        mock_comm_service.read_stream.return_value = [invalid_message]

        # Start service and let it process one message
        await test_stream_service.start()
        await asyncio.sleep(0.1)
        await test_stream_service.stop()

        # Verify error handling
        mock_comm_service.publish_to_stream.assert_not_called()

    async def test_service_recovery(self, test_stream_service, mock_comm_service, mock_txtai_service) -> None:
        """Test service recovery after errors"""
        # Simulate service error
        mock_comm_service.read_stream.side_effect = [Exception("Test error"), []]

        # Start service and let it handle error
        await test_stream_service.start()
        await asyncio.sleep(0.1)

        # Verify service continues running after error
        assert test_stream_service._running
        await test_stream_service.stop()

    async def test_message_type_handling(self, test_stream_service, mock_comm_service, mock_txtai_service) -> None:
        """Test handling of different message types"""
        message_types = [
            (MessageType.RAG_REQUEST, {"query": "test"}),
            (MessageType.LLM_REQUEST, {"prompt": "test"}),
            (MessageType.EMBEDDINGS_REQUEST, {"text": "test"}),
        ]

        for msg_type, data in message_types:
            # Reset mocks
            mock_txtai_service.handle_request.reset_mock()
            mock_comm_service.publish_to_stream.reset_mock()
            mock_comm_service.read_stream.reset_mock()

            # Setup test message for specific stream
            test_message = {"data": {"type": msg_type.value, "data": data, "session_id": "test-session"}}

            # Configure mock to return message only for appropriate stream
            stream_map = {
                MessageType.RAG_REQUEST: "rag_stream",
                MessageType.LLM_REQUEST: "llm_stream",
                MessageType.EMBEDDINGS_REQUEST: "embeddings_stream",
            }
            target_stream = stream_map[msg_type]

            async def mock_read_stream(stream: str):
                if stream == target_stream:
                    return [test_message]
                return []

            mock_comm_service.read_stream.side_effect = mock_read_stream

            # Setup response
            response_message = Message(
                type=MessageType(msg_type.value.replace("request", "response")),
                data={"result": "test"},
                session_id="test-session",
            )
            mock_txtai_service.handle_request.return_value = response_message.to_dict()

            # Process message
            await test_stream_service.start()
            await asyncio.sleep(0.1)
            await test_stream_service.stop()

            # Verify handling
            mock_txtai_service.handle_request.assert_called_once()
            mock_comm_service.publish_to_stream.assert_called_once()
