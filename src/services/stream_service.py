import logging
import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, List
from .base_service import BaseService
from .config_service import config_service
from src.models.messages import Message, MessageType
import redis

logger = logging.getLogger(__name__)


class StreamService(BaseService):
    """Service for handling stream operations"""

    def __init__(self):
        """Initialize stream service"""
        super().__init__()  # This will set up config_service
        self.streams = None
        self.consumer_group = None
        self.consumer_name = None
        self.read_count = None
        self.block_ms = None

    async def initialize(self) -> None:
        """Initialize stream service"""
        if not self.initialized:
            try:
                # Ensure config service is initialized
                if not self.config_service.initialized:
                    await self.config_service.initialize()

                # Get settings
                self.settings = self.config_service.settings

                # Initialize stream settings
                self.streams = self.settings.STREAMS
                self.consumer_group = self.settings.CONSUMER_GROUP_TXTAI
                self.consumer_name = self.settings.CONSUMER_NAME_TXTAI
                self.read_count = self.settings.STREAM_READ_COUNT
                self.block_ms = self.settings.STREAM_BLOCK_MS

                self._initialized = True
                logger.info("Stream service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize stream service: {e}")
                raise

    async def _get_redis_client(self):
        """Get Redis client from communication service"""
        from . import registry

        return registry.communication_service._redis_client

    async def start_listening(self):
        """Start listening to streams"""
        self._check_initialized()
        while True:
            try:
                redis_client = await self._get_redis_client()
                for stream in self.streams:
                    try:
                        await redis_client.xgroup_create(stream, self.consumer_group, mkstream=True)
                    except redis.ResponseError as e:
                        if "BUSYGROUP" not in str(e):
                            logger.error(f"Error creating group: {e}")
                            continue

                    messages = await self._read_stream(stream)
                    if messages:
                        await self._process_messages(messages)

                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in stream handler: {e}")
                await asyncio.sleep(1)

    async def _read_stream(self, stream: str) -> Optional[List[Message]]:
        """Read messages from stream"""
        try:
            redis_client = await self._get_redis_client()
            messages = await redis_client.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                {stream: ">"},
                count=self.read_count,
                block=self.block_ms,
            )
            return self._parse_messages(messages) if messages else None
        except Exception as e:
            logger.error(f"Error reading stream: {e}")
            return None

    def _parse_messages(self, messages: List) -> List[Message]:
        """Parse raw Redis messages into Message objects"""
        parsed_messages = []
        for stream_name, stream_messages in messages:
            for message_id, message_data in stream_messages:
                try:
                    parsed_message = Message(
                        type=message_data["type"],
                        data=json.loads(message_data["data"]),
                        session_id=message_data["session_id"],
                    )
                    parsed_messages.append(parsed_message)
                except Exception as e:
                    logger.error(f"Error parsing message {message_id}: {e}")
                    continue
        return parsed_messages

    async def _process_messages(self, messages: List[Message]):
        """Process messages from stream"""
        for message in messages:
            await self.process_message(message)

    async def process_message(self, message: Message):
        """Process a message from stream"""
        if message.type == MessageType.RAG_REQUEST:
            await self.process_rag_request(message)
        elif message.type == MessageType.RAG_CONTEXT:
            await self.process_context_message(message)
        elif message.type == MessageType.RAG_RESPONSE:
            await self.process_response_message(message)
        elif message.type == MessageType.ERROR:
            await self.process_error_message(message)

    async def process_rag_request(self, message: Message) -> AsyncGenerator[Message, None]:
        """Process a RAG request and stream responses"""
        self._check_initialized()
        try:
            # Get query from message
            query = message.data.get("query")
            if not query:
                raise ValueError("Query not found in message data")

            # Get context
            context = await self.rag_service.get_context(query)

            # Send context message
            context_message = Message(
                type=MessageType.RAG_CONTEXT,
                data={"context": context},
                session_id=message.session_id,
            )
            yield context_message

            # Generate response
            response = await self.rag_service.generate(query)

            # Send response message
            response_message = Message(
                type=MessageType.RAG_RESPONSE,
                data={"response": response},
                session_id=message.session_id,
            )
            yield response_message

        except Exception as e:
            logger.error(f"Error processing RAG request: {e}")
            error_message = Message(
                type=MessageType.ERROR, data={"error": str(e)}, session_id=message.session_id
            )
            yield error_message

    async def process_context_message(self, message: Message):
        """Process a context message from stream"""
        # Implement context message processing logic here
        pass

    async def process_response_message(self, message: Message):
        """Process a response message from stream"""
        # Implement response message processing logic here
        pass

    async def process_error_message(self, message: Message):
        """Process an error message from stream"""
        # Implement error message processing logic here
        pass


# Global service instance
stream_service = StreamService()
