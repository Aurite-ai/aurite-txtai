from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from src.middleware.auth import verify_token
from src.services import registry
from src.models.messages import MessageType
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stream"])


@router.post("/rag")
async def rag_stream(data: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
    """Handle RAG stream requests"""
    try:
        if "query" in data:
            response = await registry.rag_service.generate(data["query"])
            return {
                "type": MessageType.RAG_RESPONSE.value,
                "data": {
                    "answer": response,
                    "sources": [],
                    "context": "",
                },
                "session_id": session_id,
            }
        elif "documents" in data:
            count = await registry.embeddings_service.add(data["documents"])
            return {
                "type": MessageType.RAG_RESPONSE.value,
                "data": {
                    "answer": f"Successfully added {count} documents",
                    "sources": [],
                    "context": "",
                },
                "session_id": session_id,
            }
        else:
            return {
                "type": MessageType.ERROR.value,
                "data": {
                    "error": "Invalid request format",
                    "details": {"required": ["query or documents"]},
                },
                "session_id": session_id,
            }
    except Exception as e:
        return {
            "type": MessageType.ERROR.value,
            "data": {"error": str(e), "details": {"exception": e.__class__.__name__}},
            "session_id": session_id,
        }


@router.post("/llm")
async def llm_stream(data: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
    """Handle LLM stream requests"""
    try:
        response = await registry.llm_service.generate(
            data.get("prompt", ""), system=data.get("system", "")
        )
        return {
            "type": MessageType.LLM_RESPONSE.value,
            "data": {
                "response": response,
            },
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"Error in LLM stream: {str(e)}", exc_info=True)
        return {
            "type": MessageType.ERROR.value,
            "data": {"error": str(e)},
            "session_id": session_id,
        }


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
