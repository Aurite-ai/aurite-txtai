from __future__ import annotations

import asyncio
import logging

import pytest

from src.models.messages import MessageType
from src.services.redis.communication_service import CommunicationService, communication_service


logger = logging.getLogger(__name__)


class TestCommunicationService:
    """Test Redis communication service"""

    async def test_service_initialization(self, initialized_services) -> None:
        """Test that communication service initializes with correct Redis settings"""
        assert communication_service._initialized
        assert communication_service.consumer_group == communication_service.settings.CONSUMER_GROUP_TXTAI
        assert communication_service.consumer_name == communication_service.settings.CONSUMER_NAME_TXTAI
        assert communication_service._client is not None

    @pytest.mark.depends(on=["TestCommunicationService::test_service_initialization"])
    async def test_redis_connection(self) -> None:
        """Test Redis connection and stream creation"""
        # Test connection
        assert await communication_service._client.ping()

        # Test stream creation and info
        for stream in communication_service.settings.STREAMS:
            # Verify stream exists
            stream_exists = await communication_service._client.exists(stream)
            assert stream_exists

            # Verify consumer group
            groups = await communication_service._client.xinfo_groups(stream)
            assert any(g["name"] == communication_service.consumer_group for g in groups)

            # Verify stream info
            stream_info = await communication_service._client.xinfo_stream(stream)
            assert stream_info is not None

    @pytest.mark.depends(on=["TestCommunicationService::test_redis_connection"])
    async def test_message_format_validation(self) -> None:
        """Test message format validation"""
        stream = communication_service.settings.STREAM_RAG

        # Test valid message
        valid_msg = {
            "type": MessageType.RAG_REQUEST.value,
            "data": {"query": "test"},
            "session_id": "test",
        }
        await communication_service.publish_to_stream(stream, valid_msg)

        # Test invalid message formats
        invalid_messages = [
            {},  # Empty message
            {"type": "invalid"},  # Missing required fields
            {"type": MessageType.RAG_REQUEST.value, "data": None},  # Invalid data type
            {"type": MessageType.RAG_REQUEST.value, "data": "not_dict"},  # Wrong data type
        ]

        for msg in invalid_messages:
            with pytest.raises(Exception):
                await communication_service.publish_to_stream(stream, msg)

    @pytest.mark.depends(on=["TestCommunicationService::test_redis_connection"])
    async def test_message_acknowledgment(self) -> None:
        """Test message acknowledgment"""
        stream = communication_service.settings.STREAM_RAG

        # Publish test message
        test_msg = {
            "type": MessageType.RAG_REQUEST.value,
            "data": {"query": "test"},
            "session_id": "test",
        }
        await communication_service.publish_to_stream(stream, test_msg)

        # Read and verify acknowledgment
        messages = await communication_service.read_stream(stream)
        assert messages is not None
        assert len(messages) > 0

        # Verify message was acknowledged
        pending = await communication_service._client.xpending(
            name=stream,
            groupname=communication_service.consumer_group,
        )
        assert pending["pending"] == 0

    @pytest.mark.depends(on=["TestCommunicationService::test_redis_connection"])
    async def test_concurrent_operations(self) -> None:
        """Test concurrent publish and read operations"""
        stream = communication_service.settings.STREAM_RAG
        message_count = 5

        # Publish multiple messages concurrently
        async def publish_message(i: int) -> None:
            msg = {
                "type": MessageType.RAG_REQUEST.value,
                "data": {"query": f"test_{i}"},
                "session_id": f"test_{i}",
            }
            await communication_service.publish_to_stream(stream, msg)

        await asyncio.gather(*[publish_message(i) for i in range(message_count)])

        # Read messages
        messages = []
        for _ in range(message_count):
            batch = await communication_service.read_stream(stream)
            if batch:
                messages.extend(batch)

        assert len(messages) == message_count
        assert len({m["data"]["session_id"] for m in messages}) == message_count

    @pytest.mark.depends(on=["TestCommunicationService::test_redis_connection"])
    async def test_connection_recovery(self) -> None:
        """Test connection recovery after disconnection"""
        # Force disconnect
        await communication_service._client.close()
        communication_service._client = None

        # Attempt operation to trigger reconnection
        stream = communication_service.settings.STREAM_RAG
        test_msg = {
            "type": MessageType.RAG_REQUEST.value,
            "data": {"query": "test"},
            "session_id": "test",
        }

        # Should reconnect and succeed
        with pytest.raises(RuntimeError):
            await communication_service.publish_to_stream(stream, test_msg)

        # Reinitialize service
        await communication_service.initialize(communication_service.settings)
        assert communication_service._client is not None
        assert await communication_service._client.ping()

    @pytest.mark.depends(on=["TestCommunicationService::test_redis_connection"])
    async def test_service_shutdown(self) -> None:
        """Test proper service shutdown"""
        # Create new service instance for shutdown testing
        test_service = CommunicationService()
        await test_service.initialize(communication_service.settings)

        # Verify initialization
        assert test_service._initialized
        assert test_service._client is not None

        # Shutdown service
        await test_service.close()
        assert not test_service._initialized
        assert test_service._client is None

        # Verify operations fail after shutdown
        with pytest.raises(RuntimeError):
            await test_service.publish_to_stream(
                communication_service.settings.STREAM_RAG,
                {"type": MessageType.RAG_REQUEST.value, "data": {}, "session_id": "test"},
            )

    @pytest.mark.depends(on=["TestCommunicationService::test_redis_connection"])
    async def test_publish_and_read(self) -> None:
        """Test publishing and reading from streams"""
        # Create test message
        test_message = {
            "type": MessageType.RAG_REQUEST.value,
            "data": {"query": "test query"},
            "session_id": "test_session",
        }

        # Test publishing to each stream
        for stream in communication_service.settings.STREAMS:
            await communication_service.publish_to_stream(stream, test_message)

            # Read with consumer group
            messages = await communication_service.read_stream(stream)
            assert messages is not None
            assert len(messages) > 0

            # Verify message content
            message = messages[0]
            assert "data" in message
            assert isinstance(message["data"], dict)
            assert message["data"]["type"] == test_message["type"]
            assert message["data"]["data"] == test_message["data"]
            assert message["data"]["session_id"] == test_message["session_id"]

    @pytest.mark.depends(on=["TestCommunicationService::test_redis_connection"])
    async def test_error_handling(self) -> None:
        """Test error handling for invalid operations"""
        # Test invalid stream
        with pytest.raises(Exception):
            await communication_service.publish_to_stream(
                "invalid_stream",
                {
                    "type": MessageType.RAG_REQUEST.value,
                    "data": {"query": "test"},
                    "session_id": "test",
                },
            )

        # Test invalid message format
        with pytest.raises(Exception):
            await communication_service.publish_to_stream(
                communication_service.settings.STREAM_RAG,
                "not_a_dict",  # Invalid message format
            )

        # Test missing required fields
        with pytest.raises(Exception):
            await communication_service.publish_to_stream(
                communication_service.settings.STREAM_RAG,
                {"type": MessageType.RAG_REQUEST.value},  # Missing data and session_id
            )
