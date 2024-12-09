from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.middleware.auth import verify_token
from src.models.messages import Message, MessageType
from src.services import registry


router = APIRouter()


# Request Models
class LLMRequest(BaseModel):
    prompt: str
    system: str | None = None


class RAGRequest(BaseModel):
    query: str
    limit: int = 3


class EmbeddingRequest(BaseModel):
    text: str


# Direct API Endpoints
@router.post("/llm/complete")
async def complete_text(request: LLMRequest, token: bool = Depends(verify_token)):
    """Generate text completion directly"""
    try:
        response = await registry.llm_service.generate(request.prompt, system=request.system)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/query")
async def query_documents(request: RAGRequest, token: bool = Depends(verify_token)):
    """Query documents using RAG directly"""
    try:
        response = await registry.rag_service.generate(request.query, limit=request.limit)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embeddings/embed")
async def embed_text(request: EmbeddingRequest, token: bool = Depends(verify_token)):
    """Generate embeddings for text directly"""
    try:
        documents = [{"text": request.text, "id": "temp"}]
        count = await registry.embeddings_service.add(documents)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Stream-based API Endpoints
@router.post("/llm/stream")
async def stream_llm(request: LLMRequest, token: bool = Depends(verify_token)):
    """Process LLM request through stream"""
    try:
        message = Message(
            type=MessageType.LLM_REQUEST,
            data={"prompt": request.prompt, "system": request.system},
            session_id="api-session",
        )
        response = await registry.txtai_service.handle_request(message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/stream")
async def stream_rag(request: RAGRequest, token: bool = Depends(verify_token)):
    """Process RAG request through stream"""
    try:
        message = Message(
            type=MessageType.RAG_REQUEST,
            data={"query": request.query, "limit": request.limit},
            session_id="api-session",
        )
        response = await registry.txtai_service.handle_request(message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embeddings/stream")
async def stream_embeddings(request: EmbeddingRequest, token: bool = Depends(verify_token)):
    """Process embeddings request through stream"""
    try:
        message = Message(
            type=MessageType.EMBEDDINGS_REQUEST,
            data={"text": request.text},
            session_id="api-session",
        )
        response = await registry.txtai_service.handle_request(message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
