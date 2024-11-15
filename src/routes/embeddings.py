from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from src.services.embeddings_service import EmbeddingsService

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])
embeddings_service = EmbeddingsService()

class Document(BaseModel):
    text: str
    metadata: Optional[Dict] = None

class Documents(BaseModel):
    documents: List[Document]

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 5

class SearchResult(BaseModel):
    text: str
    scores: dict
    metadata: Optional[dict] = None

@router.post("/add")
async def add_documents(request: Documents):
    """Add documents to the embeddings database"""
    try:
        count = embeddings_service.add(request.documents)
        return {"status": "success", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search(query: SearchQuery):
    """Search the embeddings database"""
    try:
        results = embeddings_service.hybrid_search(query.query, query.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/semantic-search")
async def semantic_search(query: SearchQuery):
    """Perform semantic-only search"""
    try:
        results = embeddings_service.simple_search(query.query, query.limit)
        return {"results": [{"text": text, "score": score} for score, text in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 