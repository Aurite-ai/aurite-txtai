from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.models.messages import Message, MessageType
from src.services.redis.txtai_service import HTTP_OK, HTTP_UNAUTHORIZED, TxtAIService


@pytest.fixture
def mock_client():
    """Mock HTTP client"""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock()
    client.get = AsyncMock()
    return client


@pytest.fixture
async def test_txtai_service(test_settings, mock_client):
    """Create test txtai service instance"""
    with patch("httpx.AsyncClient", return_value=mock_client):
        service = TxtAIService()
        await service.initialize(test_settings)
        yield service
        await service.close()


class TestTxtAIService:
    """Test txtai service functionality"""

    async def test_initialization(self, test_settings, mock_client) -> None:
        """Test service initialization"""
        with patch("httpx.AsyncClient", return_value=mock_client):
            service = TxtAIService()
            assert not service.initialized

            await service.initialize(test_settings)
            assert service.initialized
            assert service._client == mock_client

    async def test_health_check_message(self, test_txtai_service, mock_client) -> None:
        """Test health check message handling"""
        # Setup mock response
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = HTTP_OK
        mock_response.json.return_value = {"status": "healthy"}
        mock_client.get.return_value = mock_response

        # Test health check message
        message = Message(type=MessageType.HEALTH_CHECK, data={}, session_id="test-session")
        response = await test_txtai_service.handle_request(message)

        assert response["type"] == MessageType.HEALTH_CHECK_RESPONSE.value
        assert response["data"]["status"] == "healthy"
        assert response["session_id"] == "test-session"

    async def test_rag_request(self, test_txtai_service, mock_client) -> None:
        """Test RAG request handling"""
        # Setup mock response
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.json.return_value = {"answer": "test answer"}
        mock_client.post.return_value = mock_response

        # Test RAG request
        message = Message(type=MessageType.RAG_REQUEST, data={"query": "test query"}, session_id="test-session")
        response = await test_txtai_service.handle_request(message)

        # Verify request
        mock_client.post.assert_called_once_with(
            "/stream/rag", json={"query": "test query"}, headers={"X-Session-ID": "test-session"}
        )

        # Verify response
        assert response["type"] == MessageType.RAG_RESPONSE.value
        assert response["data"]["answer"] == "test answer"
        assert response["session_id"] == "test-session"

    async def test_llm_request(self, test_txtai_service, mock_client) -> None:
        """Test LLM request handling"""
        # Setup mock response
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.json.return_value = {"response": "test response"}
        mock_client.post.return_value = mock_response

        # Test LLM request
        message = Message(
            type=MessageType.LLM_REQUEST,
            data={"prompt": "test prompt", "system": "test system"},
            session_id="test-session",
        )
        response = await test_txtai_service.handle_request(message)

        # Verify request
        mock_client.post.assert_called_once_with(
            "/stream/llm",
            json={"prompt": "test prompt", "system": "test system"},
            headers={"X-Session-ID": "test-session"},
        )

        # Verify response
        assert response["type"] == MessageType.LLM_RESPONSE.value
        assert response["data"]["response"] == "test response"
        assert response["session_id"] == "test-session"

    async def test_embeddings_request(self, test_txtai_service, mock_client) -> None:
        """Test embeddings request handling"""
        # Setup mock response
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.json.return_value = {"embeddings": [0.1, 0.2, 0.3]}
        mock_client.post.return_value = mock_response

        # Test embeddings request
        message = Message(type=MessageType.EMBEDDINGS_REQUEST, data={"text": "test text"}, session_id="test-session")
        response = await test_txtai_service.handle_request(message)

        # Verify request
        mock_client.post.assert_called_once_with(
            "/stream/embeddings", json={"text": "test text"}, headers={"X-Session-ID": "test-session"}
        )

        # Verify response
        assert response["type"] == MessageType.EMBEDDINGS_RESPONSE.value
        assert response["data"]["embeddings"] == [0.1, 0.2, 0.3]
        assert response["session_id"] == "test-session"

    async def test_response_message_handling(self, test_txtai_service) -> None:
        """Test handling of response messages"""
        test_data = {"result": "test"}
        response_types = [MessageType.RAG_RESPONSE, MessageType.LLM_RESPONSE, MessageType.EMBEDDINGS_RESPONSE]

        for msg_type in response_types:
            message = Message(type=msg_type, data=test_data, session_id="test-session")
            response = await test_txtai_service.handle_request(message)
            assert response == test_data

    async def test_http_error_handling(self, test_txtai_service, mock_client) -> None:
        """Test HTTP error handling"""
        # Test unauthorized error
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = HTTP_UNAUTHORIZED
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=AsyncMock(), response=mock_response
        )

        message = Message(type=MessageType.RAG_REQUEST, data={"query": "test"}, session_id="test-session")
        response = await test_txtai_service.handle_request(message)

        assert response["type"] == MessageType.ERROR.value
        assert "Unauthorized access" in response["data"]["error"]
        assert response["session_id"] == "test-session"

        # Test general HTTP error
        mock_client.post.side_effect = httpx.HTTPError("Connection failed")
        response = await test_txtai_service.handle_request(message)

        assert response["type"] == MessageType.ERROR.value
        assert "HTTP error" in response["data"]["error"]
        assert response["session_id"] == "test-session"

    async def test_invalid_message_type(self, test_txtai_service) -> None:
        """Test handling of invalid message types"""
        message = Message(
            type=MessageType.ERROR,  # ERROR is not a valid request type
            data={},
            session_id="test-session",
        )
        response = await test_txtai_service.handle_request(message)

        assert response["type"] == MessageType.ERROR.value
        assert "Unsupported message type" in response["data"]["error"]
        assert response["session_id"] == "test-session"

    async def test_service_not_initialized(self) -> None:
        """Test error when service is not initialized"""
        service = TxtAIService()
        message = Message(type=MessageType.RAG_REQUEST, data={"query": "test"}, session_id="test-session")
        response = await service.handle_request(message)

        assert response["type"] == MessageType.ERROR.value
        assert "Service not initialized" in response["data"]["error"]
        assert response["session_id"] == "test-session"
