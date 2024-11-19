"""Service registry for txtai services"""

import logging
from .base_service import BaseService
from .config_service import ConfigService
from .embeddings_service import EmbeddingsService
from .llm_service import LLMService
from .rag_service import RAGService
from .communication_service import CommunicationService
from .stream_service import StreamService
from .txtai_service import TxtAIService

logger = logging.getLogger(__name__)

# Initialize services in dependency order
config_service = ConfigService()
embeddings_service = EmbeddingsService()
llm_service = LLMService()
rag_service = RAGService()
communication_service = CommunicationService()
stream_service = StreamService()
txtai_service = TxtAIService()

# Create registry with initialized services
registry = type(
    "ServiceRegistry",
    (),
    {
        "config_service": config_service,
        "embeddings_service": embeddings_service,
        "llm_service": llm_service,
        "rag_service": rag_service,
        "communication_service": communication_service,
        "stream_service": stream_service,
        "txtai_service": txtai_service,
    },
)()

# Add registry reference to each service
for service in registry.__dict__.values():
    if isinstance(service, BaseService):
        service.registry = registry

logger.info("Service registry initialized")
