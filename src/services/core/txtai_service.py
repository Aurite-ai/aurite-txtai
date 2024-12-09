from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.models.messages import Message, MessageType
from src.services.base_service import BaseService


if TYPE_CHECKING:
    from src.config import Settings
    from src.services.core.embeddings_service import EmbeddingsService
    from src.services.core.llm_service import LLMService
    from src.services.core.rag_service import RAGService


logger = logging.getLogger(__name__)


class TxtAIService(BaseService):
    """Service for handling txtai operations through redis streams"""

    def __init__(self) -> None:
        """Initialize txtai service"""
        super().__init__()
        self.embeddings_service: EmbeddingsService | None = None
        self.llm_service: LLMService | None = None
        self.rag_service: RAGService | None = None

    async def initialize(
        self,
        settings: Settings,
        services: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Initialize txtai service with configuration

        Args:
            settings: Application settings
            services: Dictionary of initialized services
            **kwargs: Additional configuration options

        Raises:
            Exception: If initialization fails
        """
        try:
            await super().initialize(settings, **kwargs)

            if not self._initialized:
                # Set required services
                self.embeddings_service = services.get("embeddings")
                self.llm_service = services.get("llm")
                self.rag_service = services.get("rag")

                if not all([self.embeddings_service, self.llm_service, self.rag_service]):
                    raise ValueError("Required services not provided")

                self._initialized = True
                logger.info("TxtAI service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize TxtAI service: {e!s}")
            raise

    async def handle_request(self, message: Message) -> Message | None:
        """Handle incoming txtai request

        Args:
            message: Request message to handle

        Returns:
            Message | None: Response message if any
        """
        try:
            self._check_initialized()
            if not all([self.embeddings_service, self.llm_service, self.rag_service]):
                raise RuntimeError("Required services not initialized")

            # Handle different message types
            if message.type == MessageType.RAG_REQUEST:
                result = await self.rag_service.answer(
                    question=message.data["query"],
                    limit=message.data.get("limit", 3),
                    min_score=message.data.get("min_score", 0.0),
                    temperature=message.data.get("temperature", 0.7),
                )
                return Message(
                    type=MessageType.RAG_RESPONSE,
                    data=result,
                    session_id=message.session_id,
                )

            elif message.type == MessageType.LLM_REQUEST:
                response = await self.llm_service.generate(
                    prompt=message.data["prompt"],
                    system_prompt=message.data.get("system_prompt"),
                    temperature=message.data.get("temperature", 0.7),
                    max_tokens=message.data.get("max_tokens", 1000),
                )
                return Message(
                    type=MessageType.LLM_RESPONSE,
                    data={"response": response},
                    session_id=message.session_id,
                )

            elif message.type == MessageType.EMBEDDINGS_REQUEST:
                results = await self.embeddings_service.hybrid_search(
                    query=message.data["query"],
                    limit=message.data.get("limit", 5),
                    min_score=message.data.get("min_score", 0.0),
                )
                return Message(
                    type=MessageType.EMBEDDINGS_RESPONSE,
                    data={"results": results},
                    session_id=message.session_id,
                )

            logger.warning(f"Unhandled message type: {message.type}")
            return None

        except Exception as e:
            logger.error(f"Error handling request: {e!s}")
            return Message(
                type=MessageType.ERROR,
                data={"error": str(e)},
                session_id=message.session_id,
            )


# Global instance
txtai_service = TxtAIService()
