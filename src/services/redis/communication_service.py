from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import redis.asyncio as redis

from src.services.base_service import BaseService


if TYPE_CHECKING:
    from src.config import Settings


logger = logging.getLogger(__name__)


class CommunicationService(BaseService):
    """Service for handling Redis stream communication"""

    def __init__(self) -> None:
        """Initialize communication service"""
        super().__init__()
        self._redis_client: redis.Redis | None = None
        self.streams: list[str] = []
        self.consumer_group: str = ""
        self.consumer_name: str = ""

    async def initialize(self, settings: Settings) -> None:
        """Initialize Redis connection and streams"""
        if not self.initialized:
            try:
                # Connect to Redis
                self._redis_client = redis.Redis.from_url(settings.REDIS_URL, db=settings.REDIS_DB)
                await self._redis_client.ping()
                logger.info("Redis connection established")

                # Store stream configuration
                self.streams = settings.STREAMS
                self.consumer_group = settings.CONSUMER_GROUP_TXTAI
                self.consumer_name = settings.CONSUMER_NAME_TXTAI
                self.settings = settings

                # Initialize consumer groups
                await self._initialize_consumer_groups()

                self._initialized = True
                logger.info("Communication service initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Redis connection: {e}")
                raise

    async def _initialize_consumer_groups(self) -> None:
        """Initialize consumer groups for all streams"""
        for stream in self.streams:
            try:
                # Create stream and consumer group first
                await self._redis_client.xgroup_create(
                    stream, self.consumer_group, mkstream=True, id="0"
                )
                logger.info(f"Created consumer group {self.consumer_group} for stream: {stream}")

                # Now that we know the stream exists, get group info
                try:
                    groups = await self._redis_client.xinfo_groups(stream)
                    logger.info(f"Existing groups for stream {stream}: {groups}")

                    # Log stream info
                    stream_info = await self._redis_client.xinfo_stream(stream)
                    logger.info(f"Stream info for {stream}: {stream_info}")
                except redis.ResponseError as e:
                    # Just log any issues getting stream info, don't fail initialization
                    logger.warning(f"Could not get stream info for {stream}: {e}")

            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    logger.error(f"Error creating group for stream {stream}: {e}")
                    raise
                logger.info(
                    f"Consumer group {self.consumer_group} already exists for stream {stream}"
                )

    async def publish_to_stream(self, stream: str, data: dict[str, Any]) -> None:
        """Publish message to Redis Stream"""
        self._check_initialized()
        try:
            # Verify stream is valid
            if stream not in self.streams:
                raise ValueError(f"Invalid stream: {stream}")

            # Ensure data is a proper dictionary
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")

            # Format message for Redis stream
            stream_data = {
                "type": data.get("type", "unknown"),
                "data": json.dumps(data.get("data", {})),  # Serialize nested data
                "session_id": data.get("session_id", "unknown"),
            }

            await self._redis_client.xadd(stream, stream_data)
            logger.info(f"Published to stream {stream}: {data}")

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def read_from_stream(self, stream: str) -> dict[str, Any] | None:
        """Read message from Redis Stream"""
        self._check_initialized()
        try:
            # Use debug level for routine operations
            logger.debug(f"Attempting to read from stream: {stream}")

            messages = await self._redis_client.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                {stream: ">"},
                count=self.settings.STREAM_READ_COUNT,
                block=self.settings.STREAM_BLOCK_MS,
            )

            if messages:
                # Only log when we actually get messages
                logger.info(f"Raw messages from Redis: {messages}")
                stream_name, stream_messages = messages[0]
                msg_id, msg_data = stream_messages[0]

                message = {
                    "type": msg_data[b"type"].decode(),
                    "data": json.loads(msg_data[b"data"].decode()),
                    "session_id": msg_data[b"session_id"].decode(),
                }

                await self._redis_client.xack(stream, self.consumer_group, msg_id)
                return message

            return None

        except Exception as e:
            logger.error(f"Error reading from stream {stream}: {e}")
            raise

    async def close(self) -> None:
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Redis connection closed")


# Global service instance
communication_service = CommunicationService()
