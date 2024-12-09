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
                timeout=30.0,
            )
            self._initialized = True
            logger.info("TxtAI service initialized successfully")

    async def handle_request(self, message: Message) -> dict[str, Any]:
        """Handle incoming request"""
        try:
            # Skip response messages to avoid loops
            if message.type in [
                MessageType.RAG_RESPONSE,
                MessageType.LLM_RESPONSE,
                MessageType.EMBEDDINGS_RESPONSE,
            ]:
                logger.debug(f"Skipping response message type: {message.type}")
                return message.data

            # Get endpoint based on message type
            endpoint = self._get_endpoint(message.type)

            # Process request based on message type
            if message.type == MessageType.RAG_REQUEST:
                response = await self._client.post(endpoint, json={"query": message.data["query"]})
                response.raise_for_status()
                response_data = response.json()
                return {
                    "type": MessageType.RAG_RESPONSE.value,
                    "data": response_data,
                    "session_id": message.session_id,
                }
            elif message.type == MessageType.LLM_REQUEST:
                response = await self._client.post(endpoint, json=message.data)
                response.raise_for_status()
                response_data = response.json()
                return {
                    "type": MessageType.LLM_RESPONSE.value,
                    "data": response_data,
                    "session_id": message.session_id,
                }
            elif message.type == MessageType.EMBEDDINGS_REQUEST:
                response = await self._client.post(endpoint, json=message.data)
                response.raise_for_status()
                return {
                    "type": MessageType.EMBEDDINGS_RESPONSE.value,
                    "data": response.json(),
                    "session_id": message.session_id,
                }
            else:
                raise ValueError(f"Unsupported message type: {message.type}")

        except (ValueError, RuntimeError, httpx.HTTPError) as e:
            logger.error(f"Error handling request: {e}")
            return {
                "type": MessageType.ERROR.value,
                "data": {"error": str(e)},
                "session_id": message.session_id,
            }

    def _get_endpoint(self, message_type: MessageType) -> str:
        """Get endpoint for message type"""
        endpoints = {
            MessageType.RAG_REQUEST: "/stream/rag",
            MessageType.RAG_RESPONSE: "/stream/rag",
            MessageType.LLM_REQUEST: "/stream/llm",
            MessageType.LLM_RESPONSE: "/stream/llm",
            MessageType.EMBEDDINGS_REQUEST: "/stream/embeddings",
            MessageType.EMBEDDINGS_RESPONSE: "/stream/embeddings",
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
            return response.json().get("status") == "healthy"
        except (httpx.HTTPError, httpx.RequestError) as e:
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
