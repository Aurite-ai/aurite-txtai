from fastapi import FastAPI
from src.routes import embeddings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="txtai Service",
    description="API for semantic search and document embeddings using txtai",
    version="1.0.0"
)

# Include routers
app.include_router(embeddings.router)

@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Only used when running directly (not through uvicorn command)
if __name__ == "__main__":
    import uvicorn
    from src.services.config_service import config_service
    
    uvicorn.run(
        "src.main:app",
        host=config_service.settings.API_HOST,
        port=config_service.settings.API_PORT,
        reload=True
    )