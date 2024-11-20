import asyncio
import logging
from typing import Dict, Any, Optional
import json
from src.config import Settings
from ..base_service import BaseService
from .communication_service import communication_service
from .txtai_service import txtai_service
from src.models.messages import Message, MessageType
import redis

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

            # Create streams if they don't exist
            for stream in self.streams:
                try:
                    await communication_service._redis_client.xgroup_create(
                        stream, communication_service.consumer_group, mkstream=True, id="0"
                    )
                except redis.ResponseError as e:
                    if "BUSYGROUP" not in str(e):
                        raise

            self._initialized = True

    async def start_listening(self) -> None:
        """Start listening to streams"""
        self._check_initialized()
        if not self._listening:
            self._listening = True
            self._listen_task = asyncio.create_task(self._listen())
            logger.info("Stream listener started")

    async def stop_listening(self) -> None:
        """Stop listening to streams and cleanup"""
        if self._listening and self._listen_task:
            self._listening = False
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

            # Cleanup pending messages
            for stream in self.streams:
                try:
                    # Get pending messages
                    pending = await communication_service._redis_client.xpending(
                        stream, communication_service.consumer_group
                    )
                    if pending:
                        logger.info(
                            f"Cleaning up {pending['pending']} pending messages in {stream}"
                        )
                        # Acknowledge all pending messages
                        messages = await communication_service._redis_client.xpending_range(
                            stream,
                            communication_service.consumer_group,
                            min="-",
                            max="+",
                            count=pending['pending'],
                        )
                        for msg in messages:
                            await communication_service._redis_client.xack(
                                stream, communication_service.consumer_group, msg['message_id']
                            )
                except Exception as e:
                    logger.error(f"Error cleaning up stream {stream}: {e}")

            self._listen_task = None
            logger.info("Stream listener stopped and cleaned up")

    async def _listen(self) -> None:
        """Listen to streams and process messages"""
        while self._listening:
            try:
                for stream in self.streams:
                    logger.debug(f"Checking stream: {stream}")
                    message = await communication_service.read_from_stream(stream)
                    if message:
                        logger.info(f"Received message on stream {stream}: {message}")
                        await self.process_message(stream, message)

                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"Error in stream listener: {e}")
                await asyncio.sleep(2)

    async def process_message(self, stream: str, message: Dict[str, Any]) -> None:
        """Process a message from a stream"""
        try:
            logger.info(f"Processing message from stream {stream}: {message}")

            # Skip error messages
            message_type = message.get("type")
            if not message_type:
                logger.error("Message type is missing")
                return

            # Create Message object with validated type
            try:
                msg = Message.from_dict(message)
            except ValueError as e:
                logger.error(f"Invalid message format: {e}")
                error_response = {
                    "type": MessageType.ERROR.value,
                    "data": {"error": str(e)},
                    "session_id": message.get("session_id", ""),
                }
                await communication_service.publish_to_stream(stream, error_response)
                return

            # Process message through txtai service
            logger.info("Sending message to txtai service")
            response = await txtai_service.handle_request(msg)
            logger.info(f"Got response from txtai service: {response}")

            if response:
                # Publish response to stream
                logger.info(f"Publishing response to stream {stream}")
                await communication_service.publish_to_stream(stream, response)
                logger.info(f"Published response: {response}")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            error_response = {
                "type": MessageType.ERROR.value,
                "data": {"error": str(e)},
                "session_id": message.get("session_id", ""),
            }
            await communication_service.publish_to_stream(stream, error_response)


# Global service instance
stream_service = StreamService()
