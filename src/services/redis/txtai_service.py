from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from src.config import Settings
from src.models.messages import Message, MessageType
from src.services.base_service import BaseService


if TYPE_CHECKING:
    from src.config.settings import Settings


logger = logging.getLogger(__name__)

# HTTP Status Codes
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401


class TxtAIService(BaseService):
    """Service for communicating with txtai server"""

    def __init__(self) -> None:
        self._initialized = False
        self._settings: Settings | None = None
        self._client: httpx.AsyncClient | None = None
        self._services: dict[str, Any] | None = None

    @property
    def initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized

    async def initialize(self, settings: Settings, services: dict[str, Any] | None = None) -> None:
        """Initialize service with settings and optional core services"""
        if not self._initialized:
            self._settings = settings
            self._services = services
            self._client = httpx.AsyncClient(
                base_url=self._settings.TXTAI_URL,
                headers={"Authorization": f"Bearer {self._settings.API_KEY}"},
                timeout=30.0,  # Increased timeout for LLM operations
            )
            self._initialized = True
            logger.info(f"TxtAI service initialized with URL: {self._settings.TXTAI_URL}")

    async def handle_request(self, message: Message) -> dict[str, Any]:
        """Handle incoming request"""
        try:
            if not self._initialized or not self._client:
                return {
                    "type": MessageType.ERROR.value,
                    "data": {"error": "Service not initialized"},
                    "session_id": message.session_id,
                }

            # Convert string message type to enum if needed
            msg_type = MessageType.from_str(message.type) if isinstance(message.type, str) else message.type

            # Skip response messages to avoid loops
            if msg_type in [
                MessageType.RAG_RESPONSE,
                MessageType.LLM_RESPONSE,
                MessageType.EMBEDDINGS_RESPONSE,
                MessageType.HEALTH_CHECK_RESPONSE,
            ]:
                logger.debug(f"Skipping response message type: {msg_type}")
                return message.data

            # Handle health check separately
            if msg_type == MessageType.HEALTH_CHECK:
                is_healthy = await self.check_health()
                return {
                    "type": MessageType.HEALTH_CHECK_RESPONSE.value,
                    "data": {"status": "healthy" if is_healthy else "unhealthy"},
                    "session_id": message.session_id,
                }

            # Get appropriate endpoint and response type
            try:
                endpoint, response_type = self._get_endpoint_and_response(msg_type)
            except ValueError as e:
                return {
                    "type": MessageType.ERROR.value,
                    "data": {"error": str(e)},
                    "session_id": message.session_id,
                }

            # Forward request to txtai server with session ID
            response = await self._client.post(
                endpoint, json=message.data, headers={"X-Session-ID": message.session_id}
            )
            response.raise_for_status()

            # Format response with correct type
            return {
                "type": response_type,
                "data": response.json(),
                "session_id": message.session_id,
            }

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_msg = f"HTTP {status_code} error"
            if status_code == HTTP_UNAUTHORIZED:
                error_msg = "Unauthorized access to txtai server"
            logger.error(f"{error_msg}: {e}")
            return {
                "type": MessageType.ERROR.value,
                "data": {"error": error_msg},
                "session_id": message.session_id,
            }
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during request: {e}")
            return {
                "type": MessageType.ERROR.value,
                "data": {"error": f"HTTP error: {e!s}"},
                "session_id": message.session_id,
            }
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "type": MessageType.ERROR.value,
                "data": {"error": str(e)},
                "session_id": message.session_id,
            }

    def _get_endpoint_and_response(self, message_type: MessageType) -> tuple[str, str]:
        """Get appropriate endpoint and response type for message type"""
        endpoints = {
            MessageType.RAG_REQUEST: ("/stream/rag", MessageType.RAG_RESPONSE.value),
            MessageType.EMBEDDINGS_REQUEST: ("/stream/embeddings", MessageType.EMBEDDINGS_RESPONSE.value),
            MessageType.LLM_REQUEST: ("/stream/llm", MessageType.LLM_RESPONSE.value),
            MessageType.HEALTH_CHECK: ("/health", MessageType.HEALTH_CHECK_RESPONSE.value),
        }

        if message_type not in endpoints:
            raise ValueError(f"Unsupported message type: {message_type}")

        return endpoints[message_type]

    async def check_health(self) -> bool:
        """Check txtai server health"""
        if not self._client:
            return False

        try:
            response = await self._client.get("/health")
            response.raise_for_status()
            return response.status_code == HTTP_OK and response.json().get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._initialized = False
            logger.info("TxtAI service closed")


# Global instance
txtai_service = TxtAIService()
