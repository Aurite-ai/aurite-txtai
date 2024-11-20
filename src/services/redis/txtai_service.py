import logging
from typing import Dict, Any, Optional
from ..base_service import BaseService
from ..core.embeddings_service import EmbeddingsService
from ..core.llm_service import LLMService
from ..core.rag_service import RAGService
from settings import Settings
from src.models.messages import Message, MessageType

logger = logging.getLogger(__name__)


class TxtAIService(BaseService):
    """Service to bridge Redis streams with txtai services"""

    def __init__(self):
        """Initialize txtai service"""
        super().__init__()
        self.settings: Optional[Settings] = None
        self.embeddings_service: Optional[EmbeddingsService] = None
        self.llm_service: Optional[LLMService] = None
        self.rag_service: Optional[RAGService] = None

    async def initialize(
        self,
        settings: Settings = None,
        embeddings_service: Optional[EmbeddingsService] = None,
        llm_service: Optional[LLMService] = None,
        rag_service: Optional[RAGService] = None,
    ) -> None:
        """Initialize with core services"""
        if not self.initialized:
            try:
                # Get or create settings
                self.settings = settings or Settings()

                # Set service dependencies
                self.embeddings_service = embeddings_service
                self.llm_service = llm_service
                self.rag_service = rag_service

                # Verify all required services are initialized
                if not all(
                    [
                        embeddings_service and embeddings_service.initialized,
                        llm_service and llm_service.initialized,
                        rag_service and rag_service.initialized,
                    ]
                ):
                    raise ValueError("All core services must be initialized")

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
            else:
                raise ValueError(f"Unsupported message type: {message.type}")

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            raise

    async def _handle_rag_request(self, message: Message) -> Dict[str, Any]:
        """Handle RAG requests"""
        try:
            query = message.data.get("query")
            if not query:
                raise ValueError("Query is required for RAG requests")

            response = await self.rag_service.generate(query)
            return {"answer": response, "session_id": message.session_id}

        except Exception as e:
            logger.error(f"RAG request failed: {e}")
            raise

    async def _handle_llm_request(self, message: Message) -> Dict[str, Any]:
        """Handle LLM requests"""
        try:
            prompt = message.data.get("prompt")
            if not prompt:
                raise ValueError("Prompt is required for LLM requests")

            response = await self.llm_service.generate(prompt)
            return {"response": response, "session_id": message.session_id}

        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise

    async def _handle_embeddings_request(self, message: Message) -> Dict[str, Any]:
        """Handle embeddings requests"""
        try:
            documents = message.data.get("documents")
            if not documents:
                raise ValueError("Documents are required for embeddings requests")

            count = await self.embeddings_service.add(documents)
            return {"count": count, "session_id": message.session_id}

        except Exception as e:
            logger.error(f"Embeddings request failed: {e}")
            raise


# Global service instance
txtai_service = TxtAIService()
