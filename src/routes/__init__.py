from fastapi import APIRouter
from .embeddings_router import router as embeddings_router
from .rag_router import router as rag_router
from .llm_router import router as llm_router
from .test_router import router as test_router
from .stream_router import router as stream_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
api_router.include_router(llm_router, prefix="/llm", tags=["llm"])
api_router.include_router(test_router, prefix="/test", tags=["test"])
api_router.include_router(stream_router, prefix="/stream", tags=["stream"])
