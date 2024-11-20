import pytest
import json
from src.services.redis.communication_service import communication_service
from src.models.messages import Message, MessageType
import redis


@pytest.mark.asyncio
class TestCommunicationService:
    """Test communication service functionality"""

    async def test_service_initialization(self, initialized_services):
        """Test that communication service initializes with correct Redis settings"""
        assert communication_service.initialized
        assert (
            communication_service.consumer_group
            == communication_service.settings.CONSUMER_GROUP_TXTAI
        )
        assert (
            communication_service.consumer_name
            == communication_service.settings.CONSUMER_NAME_TXTAI
        )
        assert communication_service.streams == communication_service.settings.STREAMS

    async def test_redis_connection(self, initialized_services):
        """Test Redis connection and stream creation"""
        # Test connection
        assert await communication_service._redis_client.ping()

        # Test stream creation
        for stream in communication_service.streams:
            try:
                await communication_service._redis_client.xgroup_create(
                    stream, communication_service.consumer_group, mkstream=True
                )
                stream_exists = await communication_service._redis_client.exists(stream)
                assert stream_exists
            except Exception as e:
                if "BUSYGROUP" not in str(e):  # Ignore if group already exists
                    raise

    async def test_message_publishing(self, initialized_services):
        """Test publishing messages to streams"""
        test_message = Message(
            type=MessageType.RAG_REQUEST, data={"query": "test query"}, session_id="test-session"
        )

        # Test publishing to each stream
        for stream in communication_service.streams:
            await communication_service.publish_to_stream(stream, test_message)

            # Verify message was published
            messages = await communication_service._redis_client.xread({stream: "0-0"})
            assert messages is not None
            assert len(messages) > 0

            # Verify message content
            stream_name, stream_messages = messages[0]
            msg_id, msg_data = stream_messages[-1]
            assert msg_data["type"] == test_message.type.value
            assert json.loads(msg_data["data"]) == test_message.data
            assert msg_data["session_id"] == test_message.session_id

    async def test_consumer_groups(self, initialized_services):
        """Test consumer group functionality"""
        stream = communication_service.settings.STREAM_RAG

        # Create test message
        test_message = Message(
            type=MessageType.RAG_REQUEST, data={"query": "test query"}, session_id="test-session"
        )

        # Ensure consumer group exists
        try:
            await communication_service._redis_client.xgroup_create(
                stream, communication_service.consumer_group, mkstream=True, id="0"
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Publish message
        await communication_service.publish_to_stream(stream, test_message)

        # Read with consumer group
        messages = await communication_service._redis_client.xreadgroup(
            communication_service.consumer_group,
            communication_service.consumer_name,
            {stream: ">"},
            count=1,
        )

        assert messages is not None
        assert len(messages) > 0

    async def test_error_handling(self, initialized_services):
        """Test error handling in communication service"""
        # Test invalid stream
        with pytest.raises(Exception):
            await communication_service.publish_to_stream(
                "invalid_stream",
                Message(type=MessageType.RAG_REQUEST, data={"query": "test"}, session_id="test"),
            )

        # Test invalid message type
        with pytest.raises(Exception):
            await communication_service.publish_to_stream(
                communication_service.settings.STREAM_RAG,
                Message(
                    type="invalid_type", data={"query": "test"}, session_id="test"  # type: ignore
                ),
            )
