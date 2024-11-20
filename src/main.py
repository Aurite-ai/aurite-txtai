from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import router, stream_router
from src.services import initialize_services
from src.config import Settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = Settings()

# Create FastAPI app
app = FastAPI(
    title="TxtAI Service",
    description="TxtAI service for embeddings and LLM functionality",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await initialize_services(settings)
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise


# Include routers
app.include_router(router)
app.include_router(stream_router, prefix="/stream", tags=["stream"])


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "embeddings": "initialized",
            "llm": "initialized",
            "rag": "initialized",
            "communication": "initialized",
            "txtai": "initialized",
            "stream": "initialized",
        },
    }
