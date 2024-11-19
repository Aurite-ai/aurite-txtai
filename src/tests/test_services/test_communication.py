import pytest
from src.services.communication_service import communication_service
from src.services.txtai_service import txtai_service
from src.models.messages import Message, MessageType


@pytest.fixture(autouse=True)
async def setup_txtai():
    """Initialize txtai services before tests"""
    try:
        await txtai_service.initialize()
        yield
    except Exception as e:
        pytest.fail(f"Failed to initialize txtai: {e}")


@pytest.fixture(autouse=True)
async def setup_embeddings(setup_txtai):
    """Add test documents to embeddings"""
    docs = [
        {
            "id": "test1",
            "text": "Machine learning is a field of artificial intelligence",
            "metadata": {"source": "test"},
        }
    ]

    await communication_service.handle_message(
        {
            "type": MessageType.EMBEDDING_REQUEST,
            "data": {"documents": docs},
            "session_id": "test-session",
        }
    )
    yield


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
async def test_message_handling():
    """Test message handling"""
    # Add test documents first
    docs = [
        {
            "id": "test1",
            "text": "Machine learning is a field of artificial intelligence",
            "metadata": {"source": "test"},
        }
    ]

    await communication_service.handle_message(
        {
            "type": MessageType.EMBEDDING_REQUEST,
            "data": {"documents": docs},
            "session_id": "test-session",
        }
    )

    # Now test RAG request
    test_message = {
        "type": MessageType.RAG_REQUEST,
        "data": {"query": "What is machine learning?"},
        "session_id": "test-session",
    }

    result = await communication_service.handle_message(test_message)
    assert result is not None
