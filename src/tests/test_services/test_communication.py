import pytest
from src.services.communication_service import communication_service
from src.models.messages import MessageType


@pytest.mark.asyncio
async def test_redis_connection():
    """Test basic Redis connection"""
    try:
        assert communication_service.redis_client.ping()
    except Exception as e:
        pytest.fail(f"Redis connection failed: {str(e)}")


@pytest.mark.asyncio
async def test_basic_publish():
    """Test basic message publishing"""
    test_data = {
        "type": MessageType.RAG_REQUEST,
        "data": {"query": "test query"},
        "session_id": "test-session",
    }

    try:
        result = await communication_service.publish_to_node("test_stream", test_data)
        assert result is True
    except Exception as e:
        pytest.fail(f"Publishing failed: {str(e)}")


@pytest.mark.asyncio
async def test_message_handling(setup_services):
    """Test message handling"""
    # Test RAG request
    test_message = {
        "type": MessageType.RAG_REQUEST,
        "data": {"query": "What is machine learning?"},
        "session_id": "test-session",
    }

    result = await communication_service.handle_message(test_message)
    assert result is not None
    assert "query" in result
    assert "context" in result
    assert "response" in result
