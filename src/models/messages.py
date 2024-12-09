from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class MessageType(Enum):
    """Message types for stream communication"""

    RAG_REQUEST = "rag_request"
    RAG_RESPONSE = "rag_response"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    EMBEDDINGS_REQUEST = "embedding_request"
    EMBEDDINGS_RESPONSE = "embedding_response"
    ERROR = "error"
    HEALTH_CHECK = "health_check"
    HEALTH_CHECK_RESPONSE = "health_check_response"

    @classmethod
    def from_str(cls, value: str) -> MessageType:
        """Convert string to enum value"""
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid message type: {value}")


class Message(BaseModel):
    """Message model for stream communication"""

    type: MessageType
    data: dict[str, Any]
    session_id: str = ""

    class Config:
        """Pydantic config"""

        use_enum_values = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        """Create Message from dictionary, handling string message types"""
        if isinstance(data.get("type"), str):
            data = data.copy()  # Don't modify original
            data["type"] = MessageType.from_str(data["type"])
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with string message type"""
        data = self.dict()
        data["type"] = self.type.value
        return data
