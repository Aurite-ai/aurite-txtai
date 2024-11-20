from pydantic import BaseModel
from typing import Dict, Any
from enum import Enum


class MessageType(Enum):
    """Message types for stream communication"""

    RAG_REQUEST = "rag_request"
    RAG_RESPONSE = "rag_response"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    EMBEDDINGS_REQUEST = "embedding_request"
    EMBEDDINGS_RESPONSE = "embedding_response"
    ERROR = "error"


class Message(BaseModel):
    """Message model for stream communication"""

    type: MessageType
    data: Dict[str, Any]
    session_id: str = ""

    class Config:
        """Pydantic config"""

        use_enum_values = True
