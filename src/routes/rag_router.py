from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services import registry
from src.models.messages import Message, MessageType


class RAGRequest(BaseModel):
    query: str
    limit: int = 3


router = APIRouter()


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
