from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from src.middleware.auth import verify_token
from src.services import registry
from src.models.messages import MessageType

router = APIRouter(tags=["stream"])


@router.post("/rag", dependencies=[Depends(verify_token)])
async def rag_stream(data: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
    """Handle RAG stream requests"""
    try:
        if "query" in data:
            response = await registry.rag_service.generate(data["query"])
            return {
                "type": MessageType.RAG_RESPONSE.value,
                "data": {"answer": response},
                "session_id": session_id,
            }
        elif "documents" in data:
            count = await registry.embeddings_service.add(data["documents"])
            return {
                "type": MessageType.RAG_RESPONSE.value,
                "data": {"count": count},
                "session_id": session_id,
            }
        else:
            raise ValueError("Invalid RAG request format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm", dependencies=[Depends(verify_token)])
async def llm_stream(data: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
    """Handle LLM stream requests"""
    try:
        if "prompt" not in data:
            raise ValueError("Prompt is required for LLM requests")

        response = await registry.llm_service.generate(data["prompt"], system=data.get("system"))
        return {
            "type": MessageType.LLM_RESPONSE.value,
            "data": {"response": response},
            "session_id": session_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embeddings", dependencies=[Depends(verify_token)])
async def embeddings_stream(data: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
    """Handle embeddings stream requests"""
    try:
        if "documents" not in data:
            raise ValueError("Documents are required for embeddings requests")

        count = await registry.embeddings_service.add(data["documents"])
        return {
            "type": MessageType.EMBEDDINGS_RESPONSE.value,
            "data": {"count": count},
            "session_id": session_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
