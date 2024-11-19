from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from src.routes import api_router
from src.services import registry
from src.config.settings import Settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="txtai Service", description="txtai API with Redis Streams")
settings = Settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with service status"""
    return {
        "status": "healthy",
        "services": {
            "config": registry.config_service.initialized,
            "embeddings": registry.embeddings_service.initialized,
            "llm": registry.llm_service.initialized,
            "rag": registry.rag_service.initialized,
            "communication": registry.communication_service.initialized,
            "stream": registry.stream_service.initialized,
            "stream_listening": registry.stream_service.is_listening,
        },
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize services in dependency order
        await registry.config_service.initialize()
        await registry.communication_service.initialize()
        await registry.stream_service.initialize()
        await registry.embeddings_service.initialize()
        await registry.llm_service.initialize()
        await registry.rag_service.initialize()
        await registry.txtai_service.initialize()

        # Start stream listener after all services are ready
        await registry.stream_service.start_listening()
        logger.info("All services initialized and stream listener started")

    except Exception as e:
        logger.error(f"Failed to start services: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await registry.stream_service.stop_listening()
        await registry.communication_service.close()
        logger.info("Services shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
