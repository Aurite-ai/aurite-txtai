import redis
import json
import logging
from typing import Dict, Any, Optional, List
from .config_service import config_service
from ..models.messages import Message, MessageType
from .txtai_service import txtai_service
from .base_service import BaseService

logger = logging.getLogger(__name__)


class CommunicationService(BaseService):
    """Service to handle Redis communication"""

    def __init__(self):
        super().__init__()
        self.redis_client = None

    async def initialize(self):
        """Initialize Redis connection"""
        if not self.initialized:
            try:
                self.redis_client = redis.Redis(
                    host=config_service.settings.REDIS_HOST,
                    port=config_service.settings.REDIS_PORT,
                    decode_responses=True,
                )
                # Test connection
                self.redis_client.ping()
                self._initialized = True
                logger.info("Communication service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize communication service: {e}")
                raise

    async def publish_to_node(self, node: str, message: Dict[str, Any]):
        """Publish message to Redis node"""
        self._check_initialized()
        try:
            message_str = json.dumps(message)
            await self.redis_client.publish(node, message_str)
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def subscribe_to_node(self, stream: str) -> Optional[List[Dict[str, Any]]]:
        """Subscribe to messages from Node.js"""
        try:
            # Create consumer group if doesn't exist
            try:
                self.redis_client.xgroup_create(stream, self.consumer_group, mkstream=True)
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

            # Read new messages
            messages = self.redis_client.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                {stream: '>'},
                count=1,
                block=1000,  # Block for 1 second
            )

            if not messages:
                return None

            # Parse messages
            parsed_messages = []
            for stream_name, stream_messages in messages:
                for msg_id, msg_data in stream_messages:
                    try:
                        parsed_msg = {
                            'type': msg_data['type'],
                            'data': json.loads(msg_data['data']),
                            'session_id': msg_data.get('session_id', ''),
                        }
                        parsed_messages.append(parsed_msg)
                    except Exception as e:
                        logger.error(f"Error parsing message: {e}")
                        continue

            return parsed_messages

        except Exception as e:
            logger.error(f"Failed to subscribe to Redis: {str(e)}")
            return None

    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming messages based on type"""
        try:
            msg_type = message.get('type')
            if not msg_type:
                return None

            # Convert to Message object
            msg = Message(
                type=MessageType(msg_type),
                data=message['data'],
                session_id=message.get('session_id'),
            )

            # Handle through txtai service
            return await txtai_service.handle_request(msg)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return None


# Global service instance
communication_service = CommunicationService()
