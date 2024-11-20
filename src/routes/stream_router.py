from fastapi import APIRouter, Depends
from src.middleware.auth import verify_token
from src.services.redis.stream_service import stream_service
from src.models.messages import Message, MessageType
from typing import Dict, Any

router = APIRouter()


@router.post("/start")
async def start_stream(token: bool = Depends(verify_token)):
    """Start stream listener"""
    await stream_service.start_listening()
    return {"status": "started"}


@router.post("/stop")
async def stop_stream(token: bool = Depends(verify_token)):
    """Stop stream listener"""
    await stream_service.stop_listening()
    return {"status": "stopped"}


@router.get("/status")
async def stream_status(token: bool = Depends(verify_token)):
    """Get stream listener status"""
    return {"listening": stream_service._listening, "initialized": stream_service.initialized}


@router.post("/test/{stream_type}")
async def test_stream(stream_type: str, data: Dict[str, Any], token: bool = Depends(verify_token)):
    """Test stream by sending a message"""
    # Map stream types to MessageType and stream names
    stream_map = {
        "rag": (MessageType.RAG_REQUEST, "rag_stream"),
        "llm": (MessageType.LLM_REQUEST, "llm_stream"),
        "embeddings": (MessageType.EMBEDDINGS_REQUEST, "embeddings_stream"),
    }

    if stream_type not in stream_map:
        return {"error": f"Invalid stream type. Must be one of: {list(stream_map.keys())}"}

    msg_type, stream = stream_map[stream_type]
    message = Message(type=msg_type, data=data, session_id="test-session")

    await stream_service.process_message(stream, message.dict())
    return {"status": "message sent", "stream": stream, "message": message.dict()}
