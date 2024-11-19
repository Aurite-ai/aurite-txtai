import logging
from typing import Dict, Any, Optional
from .embeddings_service import embeddings_service
from .rag_service import rag_service
from ..models.messages import Message, MessageType

logger = logging.getLogger(__name__)


class TxtAIService:
    """Service to handle txtai operations"""

    def __init__(self):
        self._initialized = False

    async def initialize(self):
        """Initialize txtai services"""
        try:
            if not self._initialized:
                # Initialize embeddings service first
                await embeddings_service.initialize()
                logger.info("Embeddings service initialized")

                # Initialize RAG service
                await rag_service.initialize()
                logger.info("RAG service initialized")

                self._initialized = True
                logger.info("TxtAI services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TxtAI services: {e}")
            raise

    async def handle_request(self, message: Message) -> Optional[Dict[str, Any]]:
        """Handle incoming txtai requests"""
        try:
            if not self._initialized:
                await self.initialize()

            if message.type == MessageType.RAG_REQUEST:
                return await rag_service.generate(message.data["query"])
            elif message.type == MessageType.EMBEDDING_REQUEST:
                return await embeddings_service.add(message.data["documents"])
            elif message.type == MessageType.LLM_REQUEST:
                # Add LLM handling if needed
                pass
            return None
        except Exception as e:
            logger.error(f"Error handling txtai request: {e}")
            return None


# Global service instance
txtai_service = TxtAIService()
