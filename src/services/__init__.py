"""Service registry for txtai services"""

from .base_service import BaseService
from .config_service import config_service
from .embeddings_service import embeddings_service
from .llm_service import llm_service
from .rag_service import rag_service
from .communication_service import communication_service
from .stream_service import stream_service
from .txtai_service import txtai_service

# Registry of all services
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
