from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

from src.services.embeddings_service import EmbeddingsService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize embeddings service
embeddings = EmbeddingsService()

# Initialize txtai API with config
from txtai.api import API
api = API({
    "embeddings": {
        "path": "sentence-transformers/nli-mpnet-base-v2",
        "content": True,
        "backend": "faiss",
        "indexes": {
            "sparse": {
                "bm25": {
                    "terms": True,
                    "normalize": True
                }
            },
            "dense": {}
        },
        "batch": 32,
        "normalize": True,
        "defaults": False
    }
})

# Register our embeddings instance
api.embeddings = embeddings.embeddings

class Document(BaseModel):
    text: str
    metadata: Optional[Dict] = {}

class Documents(BaseModel):
    documents: List[Document]

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10

@router.post("/add")
async def add_documents(documents: Documents):
    """Add documents to the embeddings index"""
    try:
        # Convert to list of dicts format
        docs = [{"text": doc.text, "metadata": doc.metadata} for doc in documents.documents]
        count = embeddings.add(docs)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/semantic-search")
async def semantic_search(query: SearchQuery):
    """Perform semantic search"""
    try:
        results = embeddings.semantic_search(query.query, query.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hybrid-search")
async def hybrid_search(query: SearchQuery):
    """Perform hybrid search"""
    try:
        logger.info(f"Performing hybrid search with query: {query.query}")
        results = embeddings.hybrid_search(query.query, query.limit)
        logger.info(f"Search returned {len(results)} results")
        return {"results": results}
    except Exception as e:
        logger.error(f"Hybrid search failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/txtai/{action}")
async def txtai_api(action: str, data: dict):
    """Pass-through endpoint for txtai's built-in API actions"""
    try:
        # Execute API action
        result = api.action(action, data)
        return {"results": result}
    except Exception as e:
        logger.error(f"Error in txtai API action '{action}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 