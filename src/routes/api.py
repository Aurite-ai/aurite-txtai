from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services import registry


# Request Models
class LLMRequest(BaseModel):
    prompt: str
    system: str | None = None


class RAGRequest(BaseModel):
    query: str
    limit: int = 3


class EmbeddingRequest(BaseModel):
    text: str


# Router
router = APIRouter()


# LLM Endpoints
@router.post("/llm/complete")
async def complete_text(request: LLMRequest):
    """Generate text completion"""
    try:
        response = await registry.llm_service.generate(request.prompt)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# RAG Endpoints
@router.post("/rag/query")
async def query_documents(request: RAGRequest):
    """Query documents using RAG"""
    try:
        response = await registry.rag_service.generate(request.query)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Embeddings Endpoints
@router.post("/embeddings/embed")
async def embed_text(request: EmbeddingRequest):
    """Generate embeddings for text"""
    try:
        documents = [{"text": request.text, "id": "temp"}]
        count = await registry.embeddings_service.add(documents)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
