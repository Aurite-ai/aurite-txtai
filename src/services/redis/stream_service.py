from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from src.models.messages import Message, MessageType
from src.services.base_service import BaseService


if TYPE_CHECKING:
    from src.config import Settings
    from src.services.redis.communication_service import CommunicationService
    from src.services.redis.txtai_service import TxtAIService


logger = logging.getLogger(__name__)


class StreamService(BaseService):
    """Service for managing Redis stream operations"""

    def __init__(self) -> None:
        """Initialize stream service"""
        super().__init__()
        self.comm_service: CommunicationService | None = None
        self.txtai_service: TxtAIService | None = None
        self._running: bool = False
        self._task: asyncio.Task[None] | None = None
        self._processed_messages: set[str] = set()

    async def initialize(
        self,
        settings: Settings,
        comm_service: CommunicationService | None = None,
        txtai_service: TxtAIService | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize stream service with configuration

        Args:
            settings: Application settings
            comm_service: Optional pre-initialized communication service
            txtai_service: Optional pre-initialized txtai service
            **kwargs: Additional configuration options

        Raises:
            Exception: If initialization fails
        """
        try:
            await super().initialize(settings, **kwargs)

            if not self._initialized:
                # Set required services
                self.comm_service = comm_service
                self.txtai_service = txtai_service

                self._initialized = True
                logger.info("Stream service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize stream service: {e!s}")
            raise

    async def start(self) -> None:
        """Start stream processing"""
        try:
            self._check_initialized()
            if not self.comm_service or not self.txtai_service:
                raise RuntimeError("Required services not initialized")

            if self._running:
                logger.warning("Stream service already running")
                return

            self._running = True
            self._processed_messages.clear()  # Reset processed messages on start
            self._task = asyncio.create_task(self._process_streams())
            logger.info("Stream service started")

        except Exception as e:
            logger.error(f"Failed to start stream service: {e!s}")
            raise

    async def stop(self) -> None:
        """Stop stream processing"""
        try:
            if not self._running:
                logger.warning("Stream service not running")
                return

            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    logger.info("Stream processing cancelled")
                except Exception as e:
                    logger.error(f"Error during stream service shutdown: {e}")
                finally:
                    self._task = None
                    self._processed_messages.clear()
                    logger.info("Stream service stopped")

        except Exception as e:
            logger.error(f"Failed to stop stream service: {e!s}")

    async def _process_streams(self) -> None:
        """Process messages from all configured streams"""
        if not self.comm_service:
            raise RuntimeError("Communication service not initialized")

        while self._running:
            try:
                for stream in self.settings.STREAMS:
                    try:
                        messages = await self.comm_service.read_stream(stream)
                        if messages:
                            for msg in messages:
                                # Generate message ID from content
                                msg_id = f"{stream}:{hash(str(msg))}"
                                if msg_id not in self._processed_messages:
                                    await self._process_message(stream, msg)
                                    self._processed_messages.add(msg_id)
                    except Exception as e:
                        logger.error(f"Error processing stream {stream}: {e}")
                        continue
                await asyncio.sleep(0.1)  # Prevent CPU spinning

            except asyncio.CancelledError:
                logger.info("Stream processing cancelled")
                raise
            except Exception as e:
                logger.error(f"Stream processing error: {e!s}")
                if self._running:
                    await asyncio.sleep(1)  # Back off on error
                    continue

    async def _process_message(self, stream: str, message: dict[str, Any]) -> None:
        """Process a single stream message

        Args:
            stream: Stream name
            message: Message data to process
        """
        try:
            if not self.comm_service or not self.txtai_service:
                raise RuntimeError("Required services not initialized")

            # Convert raw message to Message type
            msg_data = message.get("data", {})
            if not isinstance(msg_data, dict):
                raise ValueError("Invalid message format")

            # Create Message instance with proper type conversion
            msg = Message(
                type=MessageType.from_str(msg_data["type"]),
                data=msg_data.get("data", {}),
                session_id=msg_data.get("session_id", ""),
            )

            # Process message with txtai service
            response = await self.txtai_service.handle_request(msg)
            if response:
                # Handle both Message objects and dictionaries
                if isinstance(response, Message):
                    response_dict = {
                        "type": response.type.value,
                        "data": response.data,
                        "session_id": response.session_id,
                    }
                else:
                    response_dict = {
                        "type": response.get("type"),
                        "data": response.get("data", {}),
                        "session_id": response.get("session_id", ""),
                    }

                await self.comm_service.publish_to_stream(stream, response_dict)

        except (ValueError, RuntimeError) as e:
            logger.error(f"Message processing error: {e}")
            if self.comm_service:
                error_response = {
                    "type": MessageType.ERROR.value,
                    "data": {"error": str(e)},
                    "session_id": message.get("data", {}).get("session_id", ""),
                }
                await self.comm_service.publish_to_stream(stream, error_response)


# Global instance
stream_service = StreamService()
