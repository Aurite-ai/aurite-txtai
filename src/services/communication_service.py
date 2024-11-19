import redis
import json
import logging
from typing import Dict, Any, Optional, List
from .config_service import config_service
from ..models.messages import Message, MessageType
from .txtai_service import txtai_service

logger = logging.getLogger(__name__)


class CommunicationService:
    """Service to handle inter-server communication"""

    def __init__(self):
        # Redis connection for Node.js communication
        self.redis_client = redis.Redis(
            host=config_service.settings.REDIS_HOST,
            port=config_service.settings.REDIS_PORT,
            db=0,
            decode_responses=True,
        )
        self.consumer_group = "txtai-group"
        self.consumer_name = "txtai-consumer"

    async def publish_to_node(self, stream: str, data: Dict[str, Any]) -> bool:
        """Publish message to Node.js via Redis Stream"""
        try:
            # Convert dict to field-value pairs for Redis stream
            stream_data = {
                'type': str(data['type']),
                'data': json.dumps(data['data']),
                'session_id': str(data.get('session_id', '')),
            }

            self.redis_client.xadd(stream, stream_data)
            logger.info(f"Published to Redis stream {stream}: {data}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {str(e)}")
            return False

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
