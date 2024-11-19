import redis.asyncio as redis
import json
import logging
from typing import AsyncGenerator
from .base_service import BaseService
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


class CommunicationService(BaseService):
    """Service for handling communication between components"""

    def __init__(self):
        """Initialize communication service"""
        super().__init__()
        self._redis_client = None
        self.consumer_group = None
        self.consumer_name = None
        self.streams = None

    async def initialize(self) -> None:
        """Initialize communication service"""
        if not self.initialized:
            try:
                # Ensure config service is initialized
                if not self.config_service.initialized:
                    await self.config_service.initialize()

                # Get settings
                self.settings = self.config_service.settings

                # Set Redis configuration
                self.consumer_group = self.settings.CONSUMER_GROUP_TXTAI
                self.consumer_name = self.settings.CONSUMER_NAME_TXTAI
                self.streams = self.settings.STREAMS

                # Initialize Redis client with async client
                self._redis_client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    db=self.settings.REDIS_DB,
                    decode_responses=True,
                    single_connection_client=True,
                )

                # Test connection
                await self._redis_client.ping()

                self._initialized = True
                logger.info("Communication service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize communication service: {e}")
                raise

    async def publish_to_stream(self, stream: str, message: Message) -> None:
        """Publish message to Redis Stream"""
        self._check_initialized()
        try:
            stream_data = {
                "type": message.type.value,
                "data": json.dumps(message.data),
                "session_id": message.session_id,
            }
            await self._redis_client.xadd(stream, stream_data)
            logger.info(f"Published to stream {stream}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def handle_message(self, message: Message) -> AsyncGenerator[Message, None]:
        """Handle incoming messages"""
        self._check_initialized()
        try:
            logger.info(f"Handling message: {message.type} for session {message.session_id}")

            if message.type == MessageType.RAG_REQUEST:
                async for response in self.stream_service.process_rag_request(message):
                    yield response
            else:
                error_message = Message(
                    type=MessageType.ERROR,
                    data={"error": f"Unsupported message type: {message.type}"},
                    session_id=message.session_id,
                )
                yield error_message

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            error_message = Message(
                type=MessageType.ERROR,
                data={"error": str(e)},
                session_id=message.session_id,
            )
            yield error_message


# Global service instance
communication_service = CommunicationService()
