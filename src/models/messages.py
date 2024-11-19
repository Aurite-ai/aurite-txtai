from pydantic import BaseModel
from typing import Dict, Any, Optional
from enum import Enum


class MessageType(str, Enum):
    EMBEDDING_REQUEST = "embedding_request"
    RAG_REQUEST = "rag_request"
    LLM_REQUEST = "llm_request"
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"


class Message(BaseModel):
    type: MessageType
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
