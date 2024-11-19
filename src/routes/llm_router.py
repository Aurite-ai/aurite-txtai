from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services import registry
from src.models.messages import Message, MessageType


class LLMRequest(BaseModel):
    prompt: str
    system: str = None


router = APIRouter()


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
