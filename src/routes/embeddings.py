from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from src.services.embeddings_service import EmbeddingsService

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])
embeddings_service = EmbeddingsService()

class Document(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Sample document text",
                "metadata": {"category": "example", "type": "document"}
            }
        }
    )

class Documents(BaseModel):
    documents: List[Document]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [
                    {
                        "text": "First document text",
                        "metadata": {"category": "example", "type": "document"}
                    },
                    {
                        "text": "Second document text",
                        "metadata": {"category": "example", "type": "document"}
                    }
                ]
            }
        }
    )

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 5
    filters: Optional[Dict[str, Any]] = None

class HybridSearchQuery(SearchQuery):
    weight: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Weight for semantic vs keyword search")

@router.post("/add")
async def add_documents(request: Documents):
    """Add documents to the embeddings database"""
    try:
        # Convert Pydantic model to dict before passing to service
        count = embeddings_service.add(request.model_dump()["documents"])
        return {"status": "success", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def hybrid_search(query: HybridSearchQuery):
    """Search using hybrid semantic + keyword matching"""
    try:
        results = embeddings_service.hybrid_search(
            query.query, 
            query.limit,
            query.weight
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/semantic-search")
async def semantic_search(query: SearchQuery):
    """Perform semantic-only search"""
    try:
        results = embeddings_service.semantic_search(query.query, query.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/advanced-search")
async def advanced_search(query: SearchQuery):
    """Perform advanced search with metadata filtering"""
    try:
        results = embeddings_service.advanced_search(
            query.query,
            query.filters,
            query.limit
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 