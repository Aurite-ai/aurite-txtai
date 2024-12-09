from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast

import redis.asyncio as redis


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

    async def xreadgroup(
        self,
        groupname: str,
        consumername: str,
        streams: dict[str, str],
        count: int | None = None,
        block: int | None = None,
    ) -> list[tuple[bytes, list[tuple[bytes, dict[bytes, bytes]]]]] | None:
        """Read messages from a stream as part of a consumer group."""
        ...

    async def xack(self, name: str, groupname: str, *message_ids: str) -> int:
        """Acknowledge one or more messages as processed."""
        ...


class CommunicationService:
    """Service for Redis stream communication"""

    def __init__(self) -> None:
        """Initialize communication service"""
        self._initialized: bool = False
        self._settings: Settings | None = None
        self._redis_client: redis.Redis | None = None
        self.streams: list[str] = []
        self.consumer_group: str = ""
        self.consumer_name: str = ""

    @property
    def initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized

    @property
    def settings(self) -> Settings:
        """Get settings, raising an error if not initialized"""
        if self._settings is None:
            raise RuntimeError("Settings not initialized")
        return self._settings

    async def initialize(self: T, settings: Settings) -> None:
        """Initialize communication service with configuration

        Args:
            settings: Application settings

        Raises:
            Exception: If initialization fails
        """
        try:
            if not self._initialized:
                # Store settings
                self._settings = settings

                # Initialize Redis client
                self._redis_client = cast(
                    redis.Redis,
                    redis.from_url(
                        settings.REDIS_URL,
                        encoding="utf-8",
                        decode_responses=True,
                    ),
                )

                # Set stream configuration
                self.streams = settings.STREAMS
                self.consumer_group = settings.CONSUMER_GROUP_TXTAI
                self.consumer_name = settings.CONSUMER_NAME_TXTAI

                # Initialize consumer groups
                await self._initialize_consumer_groups()

                self._initialized = True
                logger.info("Communication service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize communication service: {e!s}")
            raise

    async def _initialize_consumer_groups(self) -> None:
        """Initialize consumer groups for all streams"""
        if not self._redis_client:
            raise RuntimeError("Redis client not initialized")

        for stream in self.streams:
            try:
                # Create stream and consumer group first
                await self._redis_client.xgroup_create(
                    name=stream,
                    groupname=self.consumer_group,
                    mkstream=True,
                    id="0",
                )
                logger.info(f"Created consumer group {self.consumer_group} for stream: {stream}")

                # Now that we know the stream exists, get group info
                try:
                    groups = await self._redis_client.xinfo_groups(name=stream)
                    logger.info(f"Existing groups for stream {stream}: {groups}")

                    # Log stream info
                    stream_info = await self._redis_client.xinfo_stream(name=stream)
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
        if not self._redis_client:
            raise RuntimeError("Redis client not initialized")

        try:
            # Format stream data
            stream_data = {
                "data": json.dumps(data),
                "timestamp": str(data.get("timestamp", "")),
            }

            await self._redis_client.xadd(name=stream, fields=stream_data)
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
        if not self._redis_client:
            raise RuntimeError("Redis client not initialized")

        try:
            logger.debug(f"Attempting to read from stream: {stream}")

            messages = await self._redis_client.xreadgroup(
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
                    await self._redis_client.xack(name=stream, groupname=self.consumer_group, ids=msg_id.decode())

            return stream_messages

        except Exception as e:
            logger.error(f"Error reading from stream {stream}: {e!s}")
            raise


# Global instance
communication_service = CommunicationService()
