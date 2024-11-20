import asyncio
import logging
from typing import Dict, Any, Optional
import json
from src.config import Settings
from ..base_service import BaseService
from .communication_service import communication_service
from .txtai_service import txtai_service
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


class StreamService(BaseService):
    """Service for handling Redis stream operations"""

    def __init__(self):
        """Initialize stream service"""
        super().__init__()
        self._listening = False
        self._listen_task: Optional[asyncio.Task] = None
        self.settings: Optional[Settings] = None
        self.streams: Optional[list] = None

    async def initialize(self, settings: Settings) -> None:
        """Initialize stream service"""
        if not self.initialized:
            self.settings = settings
            self.streams = settings.STREAMS
            logger.info(f"Stream service initialized with streams: {self.streams}")
            self._initialized = True

    async def start_listening(self) -> None:
        """Start listening to streams"""
        self._check_initialized()
        if not self._listening:
            self._listening = True
            self._listen_task = asyncio.create_task(self._listen())
            logger.info("Stream listener started")

    async def stop_listening(self) -> None:
        """Stop listening to streams"""
        if self._listening and self._listen_task:
            self._listening = False
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None
            logger.info("Stream listener stopped")

    async def _listen(self) -> None:
        """Listen to streams and process messages"""
        while self._listening:
            try:
                for stream in self.streams:
                    logger.info(f"Checking stream: {stream}")
                    message = await communication_service.read_from_stream(stream)
                    if message:
                        logger.info(f"Received message on stream {stream}: {message}")
                        await self.process_message(stream, message)
                    else:
                        logger.debug(f"No messages on stream {stream}")
                await asyncio.sleep(0.1)  # Prevent tight loop
            except Exception as e:
                logger.error(f"Error in stream listener: {e}")
                await asyncio.sleep(1)  # Longer delay on error

    async def process_message(self, stream: str, message: Dict[str, Any]) -> None:
        """Process a message from a stream"""
        try:
            # Skip error messages
            if message.get("type") == "error":
                logger.info(f"Skipping error message: {message}")
                return

            # Create Message object
            msg = Message(
                type=message.get("type"),
                data=message.get("data", {}),
                session_id=message.get("session_id", ""),
            )

            # Process message through txtai service
            response = await txtai_service.handle_request(msg)

            if response:
                # Map request types to response types
                response_types = {
                    "rag_request": "rag_response",
                    "embedding_request": "embedding_response",
                    "llm_request": "llm_response",
                }

                # Update response type
                request_type = message.get("type", "")
                if request_type in response_types:
                    response["type"] = response_types[request_type]

                # Publish response to stream
                await communication_service.publish_to_stream(stream, response)
                logger.info(f"Published response to stream {stream}: {response}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Don't send error back to stream to prevent loops


# Global service instance
stream_service = StreamService()
