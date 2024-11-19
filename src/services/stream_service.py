import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from .base_service import BaseService
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


class StreamService(BaseService):
    """Service for handling stream operations"""

    def __init__(self):
        """Initialize stream service"""
        super().__init__()
        self.streams = None
        self.consumer_group = None
        self.consumer_name = None
        self.read_count = None
        self.block_ms = None
        self._listening = False
        self._task = None
        self._error_count = 0
        self._max_retries = 5
        self._base_delay = 1  # Start with 1 second delay

    async def _backoff_delay(self):
        """Calculate exponential backoff delay"""
        if self._error_count > 0:
            delay = min(30, self._base_delay * (2 ** (self._error_count - 1)))  # Max 30 seconds
            logger.warning(f"Backing off for {delay} seconds (attempt {self._error_count})")
            await asyncio.sleep(delay)

    async def _listen(self):
        """Main listening loop with improved error handling"""
        while self._listening:
            try:
                if not self.registry.communication_service.initialized:
                    logger.warning("Communication service not initialized, waiting...")
                    await asyncio.sleep(1)
                    continue

                for stream in self.streams:
                    messages = await self.registry.communication_service.subscribe_to_node(stream)
                    if messages:
                        for message in messages:
                            await self.handle_stream(stream, message)

                # Reset error count on successful iteration
                if self._error_count > 0:
                    logger.info("Stream service recovered from errors")
                    self._error_count = 0

                await asyncio.sleep(0.1)

            except Exception as e:
                self._error_count += 1
                logger.error(f"Error in stream handler (attempt {self._error_count}): {e}")

                if self._error_count >= self._max_retries:
                    logger.critical("Max retries reached, stopping stream service")
                    await self.stop_listening()
                    break

                await self._backoff_delay()

    async def start_listening(self):
        """Start listening to streams with initialization check"""
        if not self._listening:
            if not self.initialized:
                logger.error("Cannot start: Stream service not initialized")
                return

            self._listening = True
            self._error_count = 0
            self._task = asyncio.create_task(self._listen())
            logger.info("Stream listener started")

    async def stop_listening(self):
        """Stop listening to streams with proper cleanup"""
        if self._listening:
            logger.info("Stopping stream listener...")
            self._listening = False
            if self._task:
                try:
                    self._task.cancel()
                    await asyncio.wait([self._task], timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Stream listener shutdown timed out")
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Error during shutdown: {e}")
                finally:
                    self._task = None
                    self._error_count = 0
            logger.info("Stream listener stopped")

    async def handle_stream(self, stream: str, message: Dict[str, Any]):
        """Handle incoming stream messages"""
        try:
            msg_type = MessageType(message["type"])
            msg = Message(
                type=msg_type, data=message["data"], session_id=message.get("session_id", "")
            )

            if msg_type == MessageType.RAG_REQUEST:
                response = await self.registry.rag_service.handle_request(msg)
            elif msg_type == MessageType.EMBEDDING_REQUEST:
                response = await self.registry.embeddings_service.handle_request(msg)
            elif msg_type == MessageType.LLM_REQUEST:
                response = await self.registry.llm_service.handle_request(msg)
            else:
                logger.error(f"Unknown message type: {msg_type}")
                return

            # Send response back on same stream
            await self.registry.communication_service.publish_to_node(
                stream,
                {
                    "type": msg_type.value.replace("request", "response"),
                    "data": response,
                    "session_id": msg.session_id,
                },
            )

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # Send error response
            await self.registry.communication_service.publish_to_node(
                stream,
                {
                    "type": "error",
                    "data": {"error": str(e)},
                    "session_id": message.get("session_id", ""),
                },
            )

    async def initialize(self) -> None:
        """Initialize stream service"""
        if not self.initialized:
            try:
                # Ensure config service is initialized
                if not self.config_service.initialized:
                    await self.config_service.initialize()

                # Get settings from config service
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


# Global service instance
stream_service = StreamService()
