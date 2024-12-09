from __future__ import annotations

import logging

import pytest
import redis.asyncio as redis

from src.models.messages import MessageType
from src.services.redis.communication_service import communication_service


logger = logging.getLogger(__name__)


class TestCommunicationService:
    """Test Redis communication service"""

    async def test_service_initialization(self, initialized_services) -> None:
        """Test that communication service initializes with correct Redis settings"""
        assert communication_service._initialized
        assert (
            communication_service.consumer_group
            == communication_service.settings.CONSUMER_GROUP_TXTAI
        )

    @pytest.mark.depends(on=["TestCommunicationService::test_service_initialization"])
    async def test_redis_connection(self) -> None:
        """Test Redis connection and stream creation"""
        # Test connection
        assert communication_service._redis_client is not None
        assert await communication_service._redis_client.ping()

        # Test stream creation
        for stream in communication_service.streams:
            try:
                await communication_service._redis_client.xgroup_create(
                    name=stream,
                    groupname=communication_service.consumer_group,
                    mkstream=True,
                    id="0",
                )
                stream_exists = await communication_service._redis_client.exists(stream)
                assert stream_exists
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):  # Ignore if group already exists
                    raise

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
        for stream in communication_service.streams:
            await communication_service.publish_to_stream(stream, test_message)

            # Verify message was published
            messages = await communication_service._redis_client.xread(
                streams={stream: "0-0"},
            )
            assert messages is not None
            assert len(messages) > 0

    @pytest.mark.depends(on=["TestCommunicationService::test_publish_and_read"])
    async def test_consumer_group_read(self) -> None:
        """Test reading messages with consumer group"""
        # Use RAG stream for testing
        stream = communication_service.settings.STREAM_RAG

        # Create test message
        test_message = {
            "type": MessageType.RAG_REQUEST.value,
            "data": {"query": "test query"},
            "session_id": "test_session",
        }

        # Ensure consumer group exists
        try:
            await communication_service._redis_client.xgroup_create(
                name=stream,
                groupname=communication_service.consumer_group,
                mkstream=True,
                id="0",
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Publish message
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

    @pytest.mark.depends(on=["TestCommunicationService::test_consumer_group_read"])
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

        # Test invalid message type
        with pytest.raises(Exception):
            await communication_service.publish_to_stream(
                communication_service.settings.STREAM_RAG,
                {
                    "type": "invalid_type",
                    "data": {"query": "test"},
                    "session_id": "test",
                },
            )
