import logging
from typing import Dict, Any, Optional
from ..base_service import BaseService
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


class TxtAIService(BaseService):
    """Service for handling txtai operations through Redis streams"""

    def __init__(self):
        """Initialize TxtAI service"""
        super().__init__()
        self.embeddings_service = None
        self.llm_service = None
        self.rag_service = None

    async def initialize(self, services: Dict[str, Any]) -> None:
        """Initialize service with required dependencies"""
        if not self.initialized:
            try:
                self.embeddings_service = services.get("embeddings")
                self.llm_service = services.get("llm")
                self.rag_service = services.get("rag")

                if not all([self.embeddings_service, self.llm_service, self.rag_service]):
                    raise ValueError("Missing required services")

                self._initialized = True
                logger.info("TxtAI service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize txtai service: {e}")
                raise

    async def handle_request(self, message: Message) -> Dict[str, Any]:
        """Handle incoming stream messages"""
        self._check_initialized()
        try:
            logger.info(f"Handling {message.type} request for session {message.session_id}")

            if message.type == MessageType.RAG_REQUEST:
                return await self._handle_rag_request(message)
            elif message.type == MessageType.LLM_REQUEST:
                return await self._handle_llm_request(message)
            elif message.type == MessageType.EMBEDDINGS_REQUEST:
                return await self._handle_embeddings_request(message)
            elif message.type == MessageType.ERROR:
                logger.info(f"Received error message: {message.data}")
                return None
            else:
                raise ValueError(f"Unsupported message type: {message.type}")

        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return {
                "type": MessageType.ERROR.value,
                "data": {"error": str(e)},
                "session_id": message.session_id,
            }

    async def _handle_rag_request(self, message: Message) -> Dict[str, Any]:
        """Handle RAG requests"""
        query = message.data.get("query")
        if not query:
            raise ValueError("Query is required for RAG requests")

        response = await self.rag_service.generate(query)
        return {
            "type": "rag_response",
            "data": {"answer": response},
            "session_id": message.session_id,
        }

    async def _handle_llm_request(self, message: Message) -> Dict[str, Any]:
        """Handle LLM requests"""
        prompt = message.data.get("prompt")
        if not prompt:
            raise ValueError("Prompt is required for LLM requests")

        response = await self.llm_service.generate(prompt)
        return {
            "type": "llm_response",
            "data": {"response": response},
            "session_id": message.session_id,
        }

    async def _handle_embeddings_request(self, message: Message) -> Dict[str, Any]:
        """Handle embeddings requests"""
        documents = message.data.get("documents")
        if not documents:
            raise ValueError("Documents are required for embeddings requests")

        count = await self.embeddings_service.add(documents)
        return {
            "type": "embeddings_response",
            "data": {"count": count},
            "session_id": message.session_id,
        }


# Global service instance
txtai_service = TxtAIService()
