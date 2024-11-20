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

            if message.type == MessageType.HEALTH_CHECK:
                return {
                    "type": MessageType.HEALTH_CHECK_RESPONSE.value,
                    "data": {"status": "healthy"},
                    "session_id": message.session_id,
                }
            elif message.type == MessageType.RAG_REQUEST:
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
            raise ValueError("Query cannot be empty")

        # Get optional parameters from standard format
        options = message.data.get("options", {})
        limit = options.get("limit", 3)
        threshold = options.get("threshold", 0.5)

        try:
            # Get context from embeddings service
            context = await self.rag_service.search_context(query, limit=limit, min_score=threshold)
            if not context:
                return {
                    "type": MessageType.RAG_RESPONSE.value,
                    "data": {
                        "answer": "No relevant context found to answer the question.",
                        "sources": [],
                        "context": "",
                    },
                    "session_id": message.session_id,
                }

            # Format context for LLM
            context_text = "\n".join(doc["text"] for doc in context)
            sources = [doc.get("metadata", {}).get("source", "") for doc in context]

            # Generate response using LLM with context
            answer = await self.rag_service.generate(query)

            # Return in standard format
            return {
                "type": MessageType.RAG_RESPONSE.value,
                "data": {
                    "answer": answer,
                    "sources": sources,
                    "context": context_text,
                },
                "session_id": message.session_id,
            }

        except Exception as e:
            logger.error(f"RAG request failed: {e}")
            raise ValueError(f"RAG generation failed: {str(e)}")

    async def _handle_llm_request(self, message: Message) -> Dict[str, Any]:
        """Handle LLM requests"""
        prompt = message.data.get("prompt")
        if not prompt:
            raise ValueError("Prompt is required for LLM requests")

        response = await self.llm_service.generate(prompt)
        return {
            "type": MessageType.LLM_RESPONSE.value,
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
            "type": MessageType.EMBEDDINGS_RESPONSE.value,
            "data": {"count": count},
            "session_id": message.session_id,
        }


# Global service instance
txtai_service = TxtAIService()
