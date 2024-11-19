import redis
import zmq
import json
import logging
from typing import Any, Dict
from .config_service import config_service

logger = logging.getLogger(__name__)


class CommunicationService:
    """Service to handle inter-server communication"""

    def __init__(self):
        # Redis connection for Node.js communication
        self.redis_client = redis.Redis(
            host=config_service.settings.REDIS_HOST, port=config_service.settings.REDIS_PORT, db=0
        )

        # ZMQ for Python-Python communication
        self.zmq_context = zmq.Context()
        self.publishers = {}
        self.subscribers = {}

    def publish_to_node(self, stream: str, data: Dict[str, Any]):
        """Publish message to Node.js via Redis Stream"""
        try:
            # Convert dict to field-value pairs for Redis stream
            # Redis expects {'field1': 'value1', 'field2': 'value2'} format
            stream_data = {
                'type': str(data['type']),
                'data': json.dumps(data['data']),  # Serialize nested dict to string
                'session_id': data.get('session_id', ''),
            }

            self.redis_client.xadd(stream, stream_data)
            logger.info(f"Published to Redis stream {stream}: {data}")
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {str(e)}")
            raise

    def subscribe_to_node(self, stream: str):
        """Subscribe to messages from Node.js"""
        try:
            # Create consumer group if doesn't exist
            try:
                self.redis_client.xgroup_create(stream, "txtai-group", mkstream=True)
            except redis.exceptions.ResponseError:
                pass

            while True:
                try:
                    messages = self.redis_client.xreadgroup(
                        "txtai-group", "txtai-consumer", {stream: ">"}, count=1
                    )
                    if messages:
                        return messages
                except Exception as e:
                    logger.error(f"Error reading stream: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Failed to subscribe to Redis: {str(e)}")
            raise

    def publish_to_persona(self, topic: str, data: Dict[str, Any]):
        """Publish message to Persona server via ZMQ"""
        if topic not in self.publishers:
            socket = self.zmq_context.socket(zmq.PUB)
            socket.bind(f"tcp://*:{config_service.settings.ZMQ_BASE_PORT}")
            self.publishers[topic] = socket

        try:
            message = json.dumps(data)
            self.publishers[topic].send_string(f"{topic} {message}")
            logger.info(f"Published to ZMQ topic {topic}: {data}")
        except Exception as e:
            logger.error(f"Failed to publish to ZMQ: {str(e)}")
            raise

    def subscribe_to_persona(self, topic: str):
        """Subscribe to messages from Persona server"""
        if topic not in self.subscribers:
            socket = self.zmq_context.socket(zmq.SUB)
            socket.connect(f"tcp://localhost:{config_service.settings.ZMQ_BASE_PORT}")
            socket.setsockopt_string(zmq.SUBSCRIBE, topic)
            self.subscribers[topic] = socket

        try:
            message = self.subscribers[topic].recv_string()
            _, data = message.split(" ", 1)
            return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to receive from ZMQ: {str(e)}")
            raise


# Global service instance
communication_service = CommunicationService()
