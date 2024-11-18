# from fastapi import APIRouter, HTTPException, Security
# from typing import Dict, Optional
# from pydantic import BaseModel
# import logging

# from src.services.rag_service import rag_service
# from src.middleware.auth import get_api_key

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/api/rag", tags=["rag"])


# class RAGQuery(BaseModel):
#     question: str
#     limit: Optional[int] = 3


# @router.post("/generate")
# async def generate_response(query: RAGQuery, api_key: str = Security(get_api_key)):
#     """Generate response using RAG pipeline"""
#     try:
#         response = rag_service.generate(query.question, query.limit)
#         return response
#     except Exception as e:
#         logger.error(f"RAG generation failed: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
