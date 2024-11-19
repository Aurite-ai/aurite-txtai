import pytest
from src.services.communication_service import communication_service
from src.models.messages import MessageType


def test_redis_connection():
    """Test basic Redis connection"""
    try:
        # Simple ping test
        assert communication_service.redis_client.ping()
    except Exception as e:
        pytest.fail(f"Redis connection failed: {str(e)}")


def test_basic_publish():
    """Test basic message publishing"""
    test_data = {
        "type": MessageType.RAG_REQUEST,
        "data": {"test": "message"},
        "session_id": "test-session",
    }

    try:
        # Test publishing
        communication_service.publish_to_node("test_stream", test_data)
    except Exception as e:
        pytest.fail(f"Publishing failed: {str(e)}")


# Comment out the more complex tests for now
# async def test_rag_communication_flow...
