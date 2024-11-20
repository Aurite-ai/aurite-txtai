from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services import registry
from src.models.messages import Message, MessageType


# Request Models
class LLMRequest(BaseModel):
    prompt: str
    system: str = None


class RAGRequest(BaseModel):
    query: str
    limit: int = 3


# Router
router = APIRouter()


# LLM Endpoints
@router.post("/complete")
async def complete_text(request: LLMRequest):
    """Generate text completion"""
    try:
        message = Message(
            type=MessageType.LLM_REQUEST,
            data={"prompt": request.prompt, "system": request.system},
            session_id="api-request",
        )
        response = await registry.llm_service.handle_request(message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# RAG Endpoints
@router.post("/query")
async def query_documents(request: RAGRequest):
    """Query documents using RAG"""
    try:
        message = Message(
            type=MessageType.RAG_REQUEST,
            data={"query": request.query, "options": {"limit": request.limit}},
            session_id="api-request",
        )
        response = await registry.rag_service.handle_request(message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Embeddings Endpoints
@router.post("/embed")
async def embed_text(text: str):
    """Generate embeddings for text"""
    try:
        message = Message(
            type=MessageType.EMBEDDING_REQUEST, data={"text": text}, session_id="api-request"
        )
        response = await registry.embeddings_service.handle_request(message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
