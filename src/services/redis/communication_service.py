import redis.asyncio as redis
import json
import logging
from typing import Optional, Dict, Any
from ..base_service import BaseService
from settings import Settings

logger = logging.getLogger(__name__)


class CommunicationService(BaseService):
    """Service for handling Redis stream communication"""

    def __init__(self):
        """Initialize communication service"""
        super().__init__()
        self.settings: Optional[Settings] = None
        self._redis_client: Optional[redis.Redis] = None
        self.consumer_group: Optional[str] = None
        self.consumer_name: Optional[str] = None
        self.streams: Optional[list] = None

    async def initialize(self, settings: Settings = None) -> None:
        """Initialize Redis connection and streams"""
        if not self.initialized:
            try:
                # Get or create settings
                self.settings = settings or Settings()

                # Set Redis configuration
                self.consumer_group = self.settings.CONSUMER_GROUP_TXTAI
                self.consumer_name = self.settings.CONSUMER_NAME_TXTAI
                self.streams = self.settings.STREAMS

                # Initialize Redis client
                self._redis_client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    db=self.settings.REDIS_DB,
                    decode_responses=True,
                    single_connection_client=True,
                )

                # Test connection
                await self._redis_client.ping()
                logger.info("Redis connection established")

                # Create consumer groups for each stream
                await self._initialize_consumer_groups()

                self._initialized = True
                logger.info("Communication service initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize communication service: {e}")
                raise

    async def _initialize_consumer_groups(self) -> None:
        """Initialize consumer groups for all streams"""
        for stream in self.streams:
            try:
                await self._redis_client.xgroup_create(
                    stream,
                    self.consumer_group,
                    mkstream=True,
                    id="0",  # Start from beginning
                )
                logger.info(f"Created consumer group for stream: {stream}")
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):  # Ignore if group exists
                    raise

    async def publish_to_stream(self, stream: str, data: Dict[str, Any]) -> None:
        """Publish message to Redis Stream"""
        self._check_initialized()
        try:
            # Verify stream is valid
            if stream not in self.streams:
                raise ValueError(f"Invalid stream: {stream}")

            # Convert data to string format for Redis
            stream_data = {k: str(v) for k, v in data.items()}
            await self._redis_client.xadd(stream, stream_data)
            logger.info(f"Published to stream {stream}: {data}")

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def read_from_stream(
        self, stream: str, timeout_ms: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """Read message from Redis Stream"""
        self._check_initialized()
        try:
            # Read from stream with consumer group
            messages = await self._redis_client.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                {stream: ">"},
                count=1,
                block=timeout_ms,
            )

            if not messages:
                return None

            # Process message
            stream_name, stream_messages = messages[0]
            message_id, message_data = stream_messages[0]

            # Acknowledge message
            await self._redis_client.xack(stream_name, self.consumer_group, message_id)
            logger.info(f"Read and acknowledged message from {stream}: {message_data}")

            return message_data

        except Exception as e:
            logger.error(f"Failed to read from stream: {e}")
            raise

    async def close(self) -> None:
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Redis connection closed")


# Global service instance
communication_service = CommunicationService()
