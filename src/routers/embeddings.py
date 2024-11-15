from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from ..services.embeddings_service import EmbeddingsService

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])

# Initialize embeddings service
embeddings_service = EmbeddingsService()

class Document(BaseModel):
    text: str
    metadata: Dict[str, Any] = {}

class DocumentList(BaseModel):
    documents: List[Document]

class SearchQuery(BaseModel):
    query: str
    limit: int = 3
    hybrid_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for semantic search (0.0 to 1.0)"
    )

@router.post("/add")
async def add_documents(body: DocumentList = Body(...)):
    """Add documents to the embeddings index."""
    try:
        docs = [{"text": doc.text, "metadata": doc.metadata} for doc in body.documents]
        embeddings_service.add(docs)
        return {"status": "success", "count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_documents(query: SearchQuery):
    """Search for similar documents using hybrid search."""
    try:
        results = embeddings_service.search(
            query.query, 
            query.limit,
            query.hybrid_weight
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 