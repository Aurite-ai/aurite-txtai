from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import embeddings, llm
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