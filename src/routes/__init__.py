from fastapi import APIRouter
from .api import router as api_router
from .stream_router import router as stream_router

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(stream_router, prefix="/stream", tags=["stream"])
router.include_router(api_router, tags=["api"])

# Export the configured router
__all__ = ["router"]
