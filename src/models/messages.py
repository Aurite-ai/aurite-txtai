from pydantic import BaseModel
from typing import Dict, Any, Optional
from enum import Enum


class MessageType(str, Enum):
    """Message type enum"""

    RAG_REQUEST = "rag_request"
    RAG_RESPONSE = "rag_response"
    RAG_CONTEXT = "rag_context"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    EMBEDDINGS_REQUEST = "embeddings_request"
    EMBEDDINGS_RESPONSE = "embeddings_response"
    ERROR = "error"


class Message(BaseModel):
    """Base message model"""

    type: MessageType
    data: Dict[str, Any]
    session_id: str
