import asyncio
import logging
from typing import Dict, Any
from .communication_service import communication_service
from .txtai_service import txtai_service
from ..models.messages import Message, MessageType

logger = logging.getLogger(__name__)


class StreamService:
    """Service to handle stream operations"""

    def __init__(self):
        self.streams = {
            "embeddings_stream": self._handle_embedding,
            "rag_stream": self._handle_rag,
            "llm_stream": self._handle_llm,
        }

    async def start_listening(self):
        """Start listening to all streams"""
        while True:
            try:
                for stream in self.streams:
                    messages = await communication_service.subscribe_to_node(stream)
                    if messages:
                        await self._process_messages(stream, messages)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in stream service: {e}")
                await asyncio.sleep(1)

    async def _process_messages(self, stream: str, messages: list):
        """Process messages from a stream"""
        handler = self.streams.get(stream)
        if not handler:
            logger.error(f"No handler for stream: {stream}")
            return

        for message in messages:
            try:
                result = await handler(message)
                if result:
                    response = {
                        "type": message["type"].replace("request", "response"),
                        "data": result,
                        "session_id": message.get("session_id"),
                    }
                    await communication_service.publish_to_node(stream, response)
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _handle_embedding(self, message: Dict[str, Any]):
        """Handle embedding requests"""
        msg = Message(
            type=MessageType.EMBEDDING_REQUEST,
            data=message["data"],
            session_id=message.get("session_id"),
        )
        return await txtai_service.handle_request(msg)

    async def _handle_rag(self, message: Dict[str, Any]):
        """Handle RAG requests"""
        msg = Message(
            type=MessageType.RAG_REQUEST, data=message["data"], session_id=message.get("session_id")
        )
        return await txtai_service.handle_request(msg)

    async def _handle_llm(self, message: Dict[str, Any]):
        """Handle LLM requests"""
        msg = Message(
            type=MessageType.LLM_REQUEST, data=message["data"], session_id=message.get("session_id")
        )
        return await txtai_service.handle_request(msg)


# Global service instance
stream_service = StreamService()
