from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.services.embeddings_service import SearchService

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])
search_service = SearchService()

class Document(BaseModel):
    text: str
    metadata: Optional[dict] = None

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 5

class SearchResult(BaseModel):
    text: str
    scores: dict
    metadata: Optional[dict] = None

@router.post("/add")
async def add_documents(documents: List[Document]):
    """Add documents to the embeddings database"""
    try:
        # Convert to format expected by txtai
        docs = [(i, doc.text, doc.metadata) for i, doc in enumerate(documents)]
        search_service.embeddings.index(docs)
        search_service.embeddings.save()
        return {"status": "success", "count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search(query: SearchQuery):
    """Search the embeddings database"""
    try:
        results = search_service.hybrid_search(query.query, query.limit)
        return {"results": results}  # Wrap results in object to match test expectations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/semantic-search")
async def semantic_search(query: SearchQuery):
    """Perform semantic-only search"""
    try:
        results = search_service.simple_search(query.query, query.limit)
        return {"results": [{"text": text, "score": score} for score, text in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 