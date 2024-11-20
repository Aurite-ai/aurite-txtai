import logging
from typing import Dict, Any, Optional
import json
from ..base_service import BaseService
from ..core.embeddings_service import EmbeddingsService
from ..core.llm_service import LLMService
from ..core.rag_service import RAGService
from src.config import Settings
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
        self.settings: Optional[Settings] = None

    async def initialize(self, services: Dict[str, Any], settings: Settings = None) -> None:
        """Initialize service with required dependencies"""
        self.settings = settings or Settings()
        self.embeddings_service = services.get("embeddings")
        self.llm_service = services.get("llm")
        self.rag_service = services.get("rag")

        if not all([self.embeddings_service, self.llm_service, self.rag_service]):
            raise ValueError("Missing required services")

        self._initialized = True
        logger.info("TxtAI service initialized successfully")

    async def handle_request(self, message: Message) -> Dict[str, Any]:
        """Handle incoming stream messages"""
        self._check_initialized()
        try:
            logger.info(f"Handling {message.type} request for session {message.session_id}")

            # Ensure message.data is a dictionary
            if isinstance(message.data, str):
                try:
                    message.data = json.loads(message.data)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON in message data: {message.data}")

            if message.type == MessageType.RAG_REQUEST:
                return await self._handle_rag_request(message)
            elif message.type == MessageType.LLM_REQUEST:
                return await self._handle_llm_request(message)
            elif message.type == MessageType.EMBEDDINGS_REQUEST:
                return await self._handle_embeddings_request(message)
            else:
                raise ValueError(f"Unsupported message type: {message.type}")

        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return {"type": "error", "data": {"error": str(e)}, "session_id": message.session_id}

    async def _handle_rag_request(self, message: Message) -> Dict[str, Any]:
        """Handle RAG requests"""
        try:
            query = message.data.get("query")
            if not query:
                raise ValueError("Query is required for RAG requests")

            response = await self.rag_service.generate(query)
            return {
                "type": "response",
                "data": {"answer": response},
                "session_id": message.session_id,
            }

        except Exception as e:
            logger.error(f"RAG request failed: {str(e)}")
            return {"type": "error", "data": {"error": str(e)}, "session_id": message.session_id}

    async def _handle_llm_request(self, message: Message) -> Dict[str, Any]:
        """Handle LLM requests"""
        try:
            prompt = message.data.get("prompt")
            if not prompt:
                raise ValueError("Prompt is required for LLM requests")

            response = await self.llm_service.generate(prompt)
            return {
                "type": "response",
                "data": {"response": response},
                "session_id": message.session_id,
            }

        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}")
            return {"type": "error", "data": {"error": str(e)}, "session_id": message.session_id}

    async def _handle_embeddings_request(self, message: Message) -> Dict[str, Any]:
        """Handle embeddings requests"""
        try:
            documents = message.data.get("documents")
            if not documents:
                raise ValueError("Documents are required for embeddings requests")

            count = await self.embeddings_service.add(documents)
            return {"type": "response", "data": {"count": count}, "session_id": message.session_id}

        except Exception as e:
            logger.error(f"Embeddings request failed: {str(e)}")
            return {"type": "error", "data": {"error": str(e)}, "session_id": message.session_id}


# Global service instance
txtai_service = TxtAIService()
