from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from src.services import initialize_services
from settings import Settings
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="txtai Service", description="txtai API with Redis Streams", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services registry
services = {}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Load settings
        settings = Settings()
        logger.info("Settings loaded successfully")

        # Initialize all services
        global services
        services = await initialize_services(settings)
        logger.info("All services initialized successfully")

        # Start stream listener
        await services["stream"].start_listening()
        logger.info("Stream listener started")

    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if services.get("stream"):
            await services["stream"].stop_listening()
            logger.info("Stream listener stopped")

        if services.get("communication"):
            await services["communication"].close()
            logger.info("Communication service closed")

        logger.info("All services shut down successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not services:
        raise HTTPException(status_code=503, detail="Services not initialized")

    return {
        "status": "healthy",
        "services": {name: service.initialized for name, service in services.items()},
    }


# Import and include routers
from src.routes import api_router

app.include_router(api_router)
