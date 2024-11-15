from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional, Union
from pydantic import BaseModel

from ..middleware.auth import verify_token
from ..services.llm_service import llm_service

router = APIRouter(
    prefix="/api/llm",
    tags=["llm"],
    dependencies=[Depends(verify_token)]
)

class GenerateRequest(BaseModel):
    """Request model for text generation"""
    prompt: Union[str, List[Dict[str, str]]]

class ContextRequest(BaseModel):
    """Request model for context-based generation"""
    question: str
    context: str

@router.post("/generate")
async def generate(request: GenerateRequest):
    """Generate text from a prompt"""
    try:
        response = llm_service.generate(request.prompt)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-with-context")
async def generate_with_context(request: ContextRequest):
    """Generate text using RAG-style context"""
    try:
        response = llm_service.generate_with_context(
            question=request.question,
            context=request.context
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 