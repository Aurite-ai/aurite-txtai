import logging
import asyncio
import json
from typing import AsyncGenerator, Dict, Any
from .base_service import BaseService
from .rag_service import rag_service
from .config_service import config_service
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


class StreamService(BaseService):
    """Service for handling streaming operations"""

    def __init__(self):
        """Initialize stream service"""
        super().__init__()
        self.rag_service = rag_service
        self.config_service = config_service
        self._streams: Dict[str, asyncio.Queue] = {}

    async def initialize(self) -> None:
        """Initialize stream service"""
        if not self.initialized:
            try:
                # Get settings from config service
                self.settings = self.config_service.settings
                self._initialized = True
                logger.info("Stream service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize stream service: {e}")
                raise

    async def create_stream(self, session_id: str) -> None:
        """Create a new stream for a session"""
        self._check_initialized()
        if session_id not in self._streams:
            self._streams[session_id] = asyncio.Queue()
            logger.info(f"Created stream for session: {session_id}")

    async def delete_stream(self, session_id: str) -> None:
        """Delete a stream for a session"""
        self._check_initialized()
        if session_id in self._streams:
            del self._streams[session_id]
            logger.info(f"Deleted stream for session: {session_id}")

    async def send_message(self, message: Message) -> None:
        """Send a message to a stream"""
        self._check_initialized()
        if message.session_id not in self._streams:
            await self.create_stream(message.session_id)

        await self._streams[message.session_id].put(message)
        logger.info(f"Sent message to session {message.session_id}: {message.type}")

    async def get_messages(self, session_id: str) -> AsyncGenerator[Message, None]:
        """Get messages from a stream"""
        self._check_initialized()
        if session_id not in self._streams:
            await self.create_stream(session_id)

        try:
            while True:
                message = await self._streams[session_id].get()
                yield message
                self._streams[session_id].task_done()
        except asyncio.CancelledError:
            logger.info(f"Stream cancelled for session: {session_id}")
            await self.delete_stream(session_id)
            raise

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


# Global service instance
stream_service = StreamService()
