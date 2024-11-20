from fastapi import APIRouter
from .api import router as api_router
from .stream_router import router as stream_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(stream_router, prefix="/stream", tags=["stream"])
api_router.include_router(api_router, prefix="/api", tags=["api"])
