from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from ..services.embeddings_service import EmbeddingsService

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])

# Initialize embeddings service
embeddings_service = EmbeddingsService()

class Document(BaseModel):
    text: str
    metadata: Dict[str, Any] = {}

class SearchQuery(BaseModel):
    query: str
    limit: int = 3

@router.post("/add")
async def add_documents(documents: List[Document]):
    """Add documents to the embeddings index."""
    try:
        docs = [{"text": doc.text, **doc.metadata} for doc in documents]
        embeddings_service.add(docs)
        return {"status": "success", "count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_documents(query: SearchQuery):
    """Search for similar documents."""
    try:
        results = embeddings_service.search(query.query, query.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 