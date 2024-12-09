from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

import redis.asyncio as redis

from src.services.base_service import BaseService


if TYPE_CHECKING:
    from src.config import Settings


logger = logging.getLogger(__name__)


T = TypeVar("T", bound="CommunicationService")


class RedisClientProtocol(Protocol):
    """Protocol for Redis client operations"""

    async def ping(self) -> bool:
        """Check Redis connection."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        ...

    async def xgroup_create(self, name: str, groupname: str, message_id: str = "$", mkstream: bool = False) -> bool:
        """Create a consumer group for a stream."""
        ...

    async def xinfo_groups(self, name: str) -> list[dict[str, Any]]:
        """Get information about consumer groups of a stream."""
        ...

    async def xinfo_stream(self, name: str) -> dict[str, Any]:
        """Get information about a stream."""
        ...

    async def xadd(self, name: str, fields: dict[str, str], message_id: str = "*") -> str:
        """Add a message to a stream."""
        ...

    async def xread(
        self, streams: dict[str, str], count: int | None = None, block: int | None = None
    ) -> list[tuple[bytes, list[tuple[bytes, dict[bytes, bytes]]]]] | None:
        """Read messages from one or more streams."""
        ...


class CommunicationService(BaseService):
    """Service for Redis communication and stream operations"""

    def __init__(self) -> None:
        """Initialize communication service"""
        super().__init__()
        self._client: redis.Redis | None = None
        self.consumer_group: str = ""
        self.consumer_name: str = ""

    async def initialize(self, settings: Settings, **kwargs: Any) -> None:
        """Initialize Redis connection and stream configuration

        Args:
            settings: Application settings
            **kwargs: Additional configuration options

        Raises:
            Exception: If initialization fails
        """
        try:
            await super().initialize(settings, **kwargs)

            if not self._initialized:
                # Initialize Redis client
                self._client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    db=self.settings.REDIS_DB,
                    decode_responses=True,
                )

                # Test connection
                if not await self._client.ping():
                    raise RuntimeError("Failed to connect to Redis")

                # Set consumer configuration
                self.consumer_group = self.settings.CONSUMER_GROUP_TXTAI
                self.consumer_name = self.settings.CONSUMER_NAME_TXTAI

                # Initialize streams
                for stream in self.settings.STREAMS:
                    await self._init_stream(stream)

                self._initialized = True
                logger.info("Communication service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize communication service: {e!s}")
            raise

    async def _init_stream(self, stream: str) -> None:
        """Initialize a stream configuration

        Args:
            stream: Stream to initialize

        Raises:
            Exception: If stream initialization fails
        """
        try:
            # Create stream and consumer group first
            await self._client.xgroup_create(
                name=stream,
                groupname=self.consumer_group,
                mkstream=True,
                id="0",
            )
            logger.info(f"Created consumer group {self.consumer_group} for stream: {stream}")

            # Now that we know the stream exists, get group info
            try:
                groups = await self._client.xinfo_groups(name=stream)
                logger.info(f"Existing groups for stream {stream}: {groups}")

                # Log stream info
                stream_info = await self._client.xinfo_stream(name=stream)
                logger.info(f"Stream info for {stream}: {stream_info}")
            except redis.ResponseError as e:
                # Just log any issues getting stream info, don't fail initialization
                logger.warning(f"Error getting stream info for {stream}: {e!s}")

        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
            logger.info(f"Consumer group {self.consumer_group} already exists for stream: {stream}")

    async def publish_to_stream(self, stream: str, data: dict[str, Any]) -> None:
        """Publish message to stream

        Args:
            stream: Stream to publish to
            data: Message data to publish

        Raises:
            RuntimeError: If service is not initialized
            Exception: If publishing fails
        """
        if not self._client:
            raise RuntimeError("Redis client not initialized")

        try:
            # Format stream data
            stream_data = {
                "data": json.dumps(data),
                "timestamp": str(data.get("timestamp", "")),
            }

            await self._client.xadd(name=stream, fields=stream_data)
            logger.info(f"Published to stream {stream}: {data}")

        except Exception as e:
            logger.error(f"Error publishing to stream {stream}: {e!s}")
            raise

    async def read_stream(self, stream: str) -> list[dict[str, Any]] | None:
        """Read messages from stream

        Args:
            stream: Stream to read from

        Returns:
            list[dict[str, Any]] | None: List of messages or None if no messages

        Raises:
            RuntimeError: If service is not initialized
            Exception: If reading fails
        """
        if not self._client:
            raise RuntimeError("Redis client not initialized")

        try:
            logger.debug(f"Attempting to read from stream: {stream}")

            messages = await self._client.xreadgroup(
                groupname=self.consumer_group,
                consumername=self.consumer_name,
                streams={stream: ">"},
                count=self.settings.STREAM_READ_COUNT,
                block=self.settings.STREAM_BLOCK_MS,
            )

            if not messages:
                return None

            # Process messages
            stream_messages = []
            for _, message_list in messages:
                for msg_id, msg_data in message_list:
                    # Parse message data
                    msg_data_str = {k.decode(): v.decode() for k, v in msg_data.items()}
                    message = {
                        "id": msg_id.decode(),
                        "data": json.loads(msg_data_str["data"]),
                        "timestamp": msg_data_str.get("timestamp", ""),
                    }
                    stream_messages.append(message)

                    # Acknowledge message
                    await self._client.xack(name=stream, groupname=self.consumer_group, ids=msg_id.decode())

            return stream_messages

        except Exception as e:
            logger.error(f"Error reading from stream {stream}: {e!s}")
            raise

    async def close(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._initialized = False
            logger.info("Communication service closed")


# Global instance
communication_service = CommunicationService()
