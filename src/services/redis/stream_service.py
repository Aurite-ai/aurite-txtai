import asyncio
import logging
from typing import Dict, Any, List, Optional
from ..base_service import BaseService
from .communication_service import communication_service
from .txtai_service import txtai_service
from settings import Settings
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


class StreamService(BaseService):
    """Service for handling Redis stream operations"""

    def __init__(self):
        """Initialize stream service"""
        super().__init__()
        self.settings: Optional[Settings] = None
        self._listening: bool = False
        self._task: Optional[asyncio.Task] = None
        self.streams: List[str] = []
        self.read_count: int = 1
        self.block_ms: int = 1000

    async def initialize(self, settings: Settings = None) -> None:
        """Initialize stream service with settings"""
        if not self.initialized:
            try:
                # Get or create settings
                self.settings = settings or Settings()

                # Set stream configuration
                self.streams = self.settings.STREAMS
                self.read_count = self.settings.STREAM_READ_COUNT
                self.block_ms = self.settings.STREAM_BLOCK_MS

                self._initialized = True
                logger.info(f"Stream service initialized with streams: {self.streams}")

            except Exception as e:
                logger.error(f"Failed to initialize stream service: {e}")
                raise

    async def start_listening(self) -> None:
        """Start listening to streams"""
        if self._listening:
            logger.warning("Stream listener already running")
            return

        self._listening = True
        self._task = asyncio.create_task(self._listen())
        logger.info("Stream listener started")

    async def stop_listening(self) -> None:
        """Stop listening to streams"""
        if not self._listening:
            return

        self._listening = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stream listener stopped")

    async def _listen(self) -> None:
        """Main listening loop"""
        while self._listening:
            try:
                for stream in self.streams:
                    # Read messages from stream
                    message = await communication_service.read_from_stream(
                        stream, timeout_ms=self.block_ms
                    )

                    if message:
                        await self._process_message(stream, message)

                await asyncio.sleep(0.1)  # Prevent CPU overload

            except Exception as e:
                logger.error(f"Error in stream listener: {e}")
                await asyncio.sleep(1)  # Back off on error

    async def _process_message(self, stream: str, message: Dict[str, Any]) -> None:
        """Process a single message from stream"""
        try:
            # Validate message type
            try:
                msg_type = MessageType(message["type"])
            except ValueError:
                raise ValueError(f"Invalid message type: {message['type']}")

            # Create validated message
            msg = Message(
                type=msg_type,
                data=message.get("data", {}),
                session_id=message.get("session_id", ""),
            )

            # Process through txtai service
            result = await txtai_service.handle_request(msg)

            # Determine response stream
            service_type = msg_type.value.split("_")[0]  # e.g., 'rag' from 'rag_request'
            response_stream = f"{service_type}_stream"

            if response_stream not in self.streams:
                raise ValueError(f"Invalid response stream: {response_stream}")

            # Format and send response
            response = {
                "type": f"{service_type}_response",
                "data": result,
                "session_id": msg.session_id,
            }

            await communication_service.publish_to_stream(response_stream, response)
            logger.info(f"Published response to {response_stream}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Send error response
            error_response = {
                "type": "error",
                "data": {"error": str(e)},
                "session_id": message.get("session_id", ""),
            }
            await communication_service.publish_to_stream(stream, error_response)


# Global service instance
stream_service = StreamService()
