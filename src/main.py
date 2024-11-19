from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import embeddings, llm, rag, test
import logging
from src.services import stream_service
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="txtai Service",
    description="API for semantic search and document embeddings using txtai",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(embeddings.router)
app.include_router(llm.router)
app.include_router(rag.router)
app.include_router(test.router, prefix="/api")


@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Add to startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Start stream service in background task
        asyncio.create_task(stream_service.start_listening())
        logger.info("Stream service started")
    except Exception as e:
        logger.error(f"Failed to start stream service: {e}")


# Only used when running directly (not through uvicorn command)
if __name__ == "__main__":
    import uvicorn
    from src.services.config_service import config_service

    uvicorn.run(
        "src.main:app",
        host=config_service.settings.API_HOST,
        port=config_service.settings.API_PORT,
        reload=True,
    )
