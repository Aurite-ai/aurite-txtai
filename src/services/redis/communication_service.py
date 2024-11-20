import redis.asyncio as redis
import json
import logging
from typing import Optional, Dict, Any, List
from src.services.base_service import BaseService
from src.config import Settings

logger = logging.getLogger(__name__)


class CommunicationService(BaseService):
    """Service for handling Redis stream communication"""

    def __init__(self):
        """Initialize communication service"""
        super().__init__()
        self._redis_client: Optional[redis.Redis] = None
        self.streams: List[str] = []
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

                # Clean up and initialize streams
                await self._cleanup_streams()
                await self._initialize_consumer_groups()

                self._initialized = True
                logger.info("Communication service initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Redis connection: {e}")
                raise

    async def _cleanup_streams(self) -> None:
        """Clean up existing streams"""
        for stream in self.streams:
            try:
                # Delete existing stream
                await self._redis_client.delete(stream)
                logger.info(f"Cleaned up stream: {stream}")
            except Exception as e:
                logger.error(f"Failed to clean up stream {stream}: {e}")
                raise

    async def _initialize_consumer_groups(self) -> None:
        """Initialize consumer groups for all streams"""
        for stream in self.streams:
            try:
                # Create stream and consumer group
                await self._redis_client.xgroup_create(
                    stream,
                    self.consumer_group,
                    mkstream=True,
                    id="$",  # Start from new messages only
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

    async def read_from_stream(self, stream: str) -> Optional[Dict[str, Any]]:
        """Read message from Redis Stream"""
        self._check_initialized()
        try:
            logger.info(f"Attempting to read from stream: {stream}")
            # Read messages
            messages = await self._redis_client.xreadgroup(
                self.consumer_group, self.consumer_name, {stream: ">"}, count=1, block=1000
            )

            if messages:
                logger.info(f"Raw messages from Redis: {messages}")
                stream_name, stream_messages = messages[0]
                msg_id, msg_data = stream_messages[0]

                # Parse message data
                message = {
                    "type": msg_data[b"type"].decode(),
                    "data": json.loads(msg_data[b"data"].decode()),
                    "session_id": msg_data[b"session_id"].decode(),
                }
                logger.info(f"Parsed message: {message}")
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
