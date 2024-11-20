import asyncio
import logging
from typing import Dict, Any, List, Optional
from ..base_service import BaseService
from .communication_service import communication_service
from .txtai_service import txtai_service
from src.config import Settings
from src.models.messages import Message, MessageType
import json

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
                    message = await communication_service.read_from_stream(stream)
                    if message:
                        await self.process_message(stream, message)
            except Exception as e:
                logger.error(f"Error in stream listener: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error

    async def process_message(self, stream: str, message: Dict[str, Any]) -> None:
        """Process a message from a stream"""
        try:
            # First, try to parse the message data if it's a string
            data = message.get('data')
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in message data: {data}")
                    return

            # Create Message object with parsed data
            msg = Message(type=message.get('type'), data=data, session_id=message.get('session_id'))

            # Process the message
            response = await txtai_service.handle_request(msg)

            # Publish response
            if response:
                await communication_service.publish(stream, response)

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Send a simple error response to avoid recursive validation errors
            error_response = {
                "type": "error",
                "data": str(e),
                "session_id": message.get('session_id', 'unknown'),
            }
            await communication_service.publish(stream, error_response)


# Global service instance
stream_service = StreamService()
