import logging
from typing import AsyncGenerator
from .base_service import BaseService
from .stream_service import stream_service
from .config_service import config_service
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


class CommunicationService(BaseService):
    """Service for handling communication between components"""

    def __init__(self):
        """Initialize communication service"""
        super().__init__()
        self.stream_service = stream_service
        self.config_service = config_service

    async def initialize(self) -> None:
        """Initialize communication service"""
        if not self.initialized:
            try:
                # Get settings from config service
                self.settings = self.config_service.settings
                self._initialized = True
                logger.info("Communication service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize communication service: {e}")
                raise

    async def handle_message(self, message: Message) -> AsyncGenerator[Message, None]:
        """Handle incoming messages"""
        self._check_initialized()
        try:
            logger.info(f"Handling message: {message.type} for session {message.session_id}")

            if message.type == MessageType.RAG_REQUEST:
                async for response in self.stream_service.process_rag_request(message):
                    yield response
            else:
                error_message = Message(
                    type=MessageType.ERROR,
                    data={"error": f"Unsupported message type: {message.type}"},
                    session_id=message.session_id,
                )
                yield error_message

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            error_message = Message(
                type=MessageType.ERROR,
                data={"error": str(e)},
                session_id=message.session_id,
            )
            yield error_message


# Global service instance
communication_service = CommunicationService()
