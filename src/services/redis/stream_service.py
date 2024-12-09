from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from src.models.messages import Message, MessageType
from src.services.base_service import BaseService


if TYPE_CHECKING:
    from src.config import Settings


logger = logging.getLogger(__name__)


class StreamService(BaseService):
    """Service for handling Redis stream operations"""

    def __init__(self) -> None:
        """Initialize stream service"""
        super().__init__()
        self._listening = False
        self._listen_task: asyncio.Task | None = None
        self.settings: Settings | None = None
        self.streams: list | None = None
        self.comm_service = None
        self.txtai_service = None

    async def initialize(self, settings: Settings, comm_service, txtai_service) -> None:
        """Initialize stream service with dependencies"""
        if not self.initialized:
            self.settings = settings
            self.comm_service = comm_service
            self.txtai_service = txtai_service
            self.streams = settings.STREAMS
            logger.info(f"Stream service initialized with streams: {self.streams}")
            self._initialized = True

    async def start_listening(self) -> None:
        """Start listening to streams"""
        self._check_initialized()
        if not self._listening:
            self._listening = True
            self._listen_task = asyncio.create_task(self._listen_to_streams())
            logger.info("Started listening to streams")

    async def stop_listening(self) -> None:
        """Stop listening to streams"""
        if self._listening and self._listen_task:
            self._listening = False
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped listening to streams")

    async def _listen_to_streams(self) -> None:
        """Listen to streams and process messages"""
        self._check_initialized()
        while self._listening:
            try:
                for stream in self.streams:
                    messages = await self.comm_service.read_stream(stream, block=1000)
                    if messages:
                        for message in messages:
                            await self._process_message(stream, message)
            except Exception as e:
                logger.error(f"Error processing stream messages: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error

    async def _process_message(self, stream: str, message: dict[str, Any]) -> None:
        """Process a single message from a stream"""
        try:
            msg = Message.from_dict(message)

            # Skip processing response messages to avoid loops
            if msg.type in [
                MessageType.RAG_RESPONSE,
                MessageType.LLM_RESPONSE,
                MessageType.EMBEDDINGS_RESPONSE,
                MessageType.ERROR,
            ]:
                logger.debug(f"Skipping response message type: {msg.type}")
                return

            # Process through txtai service
            response = await self.txtai_service.handle_request(msg)

            if response:
                logger.debug(f"Response before publishing: {response}")
                await self.comm_service.publish_to_stream(stream, response)

        except Exception as e:
            logger.error(f"Error processing message: {e!s}", exc_info=True)


# Global service instance
stream_service = StreamService()
