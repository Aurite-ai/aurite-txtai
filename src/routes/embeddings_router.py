from fastapi import APIRouter, HTTPException
from src.services import registry
from src.models.messages import Message, MessageType

router = APIRouter()


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
