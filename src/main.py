from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import signal
import sys
from src.services import initialize_services
from src.config import Settings
import asyncio
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global services registry
services = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app"""
    try:
        # Load settings
        settings = Settings()
        logger.info("Settings loaded successfully")

        # Initialize all services
        global services
        services = await initialize_services(settings)
        logger.info("All services initialized successfully")

        # Start stream listener
        if services.get("stream"):
            await services["stream"].start_listening()
            logger.info("Stream listener started")

        yield  # Server is running here

    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    finally:
        # Cleanup
        try:
            if services.get("stream"):
                logger.info("Stopping stream listener...")
                await services["stream"].stop_listening()
                logger.info("Stream listener stopped")

            if services.get("communication"):
                logger.info("Closing Redis connection...")
                await services["communication"].close()
                logger.info("Redis connection closed")

            logger.info("All services shut down successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Initialize FastAPI app with lifespan manager
app = FastAPI(
    title="txtai Service",
    description="txtai API with Redis Streams",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not services:
        raise HTTPException(status_code=503, detail="Services not initialized")

    return {
        "status": "healthy",
        "services": {
            name: "initialized" if service.initialized else "not initialized"
            for name, service in services.items()
        },
    }


@app.get("/")
async def root():
    """Root endpoint for service status"""
    return {
        "status": "online",
        "version": app.version,
        "services": {
            name: "initialized" if service.initialized else "not initialized"
            for name, service in services.items()
        },
    }


# Import and include routers
from src.routes import router as api_router

app.include_router(api_router, prefix="/api")

# Add startup logging
logger.info("Application initialized and ready to start")
