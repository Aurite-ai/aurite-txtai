import os
from fastapi import APIRouter, HTTPException, Security
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

from src.services.embeddings_service import embeddings_service
from src.middleware.auth import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/embeddings",
    tags=["embeddings"]
)

class Document(BaseModel):
    text: str
    metadata: Optional[Dict] = {}

class Documents(BaseModel):
    documents: List[Document]

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10

@router.post("/add")
async def add_documents(
    documents: Documents,
    api_key: str = Security(get_api_key)
):
    """Add documents to the embeddings index"""
    try:
        # Convert to list of dicts format
        docs = [{"text": doc.text, "metadata": doc.metadata} for doc in documents.documents]
        count = embeddings_service.add(docs)
        return {"count": count}
    except Exception as e:
        logger.error(f"Failed to add documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hybrid-search")
async def hybrid_search(
    query: SearchQuery,
    api_key: str = Security(get_api_key)
):
    """Perform hybrid search on the embeddings index"""
    try:
        results = embeddings_service.hybrid_search(query.query, query.limit)
        return {"results": results}
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))