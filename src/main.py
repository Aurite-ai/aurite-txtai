"""TxtAI service main application module.

This module initializes and configures the FastAPI application, sets up middleware,
and defines core endpoints including health checks and service initialization.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import Settings
from src.routes import router, stream_router
from src.services import initialize_services, registry
from src.services.redis.communication_service import CommunicationService
from src.services.redis.stream_service import StreamService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Async context manager for FastAPI lifespan.

    This handles startup and shutdown events for the application.

    Args:
        app: FastAPI application instance
    """
    try:
        # Startup
        logger.info("Starting up services...")
        await initialize_services(settings)
        logger.info("All services initialized successfully")
        yield
    except Exception as e:
        logger.error("Service initialization failed: %s", str(e))
        raise
    finally:
        # Shutdown
        logger.info("Shutting down services...")
        try:
            # Get services with proper type hints
            stream_service = cast(StreamService, registry.get_service("stream"))
            comm_service = cast(CommunicationService, registry.get_service("communication"))

            # Shutdown services if they exist
            if stream_service:
                await stream_service.stop_listening()
            if comm_service:
                await comm_service.close()

            logger.info("Services shut down successfully")
        except (RuntimeError, ConnectionError) as e:
            logger.error("Error during service shutdown: %s", str(e))


# Create FastAPI app with lifespan
app = FastAPI(
    title="TxtAI Service",
    description="TxtAI service for embeddings and LLM functionality",
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

# Include routers
app.include_router(router)
app.include_router(stream_router, prefix="/stream", tags=["stream"])


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint.

    Returns:
        dict[str, Any]: Health status of all services

    Raises:
        HTTPException: If any service is not healthy
    """
    try:
        # Check service health
        services_status = await registry.check_health()

        # Check if any service is unhealthy
        unhealthy_services = {name: status for name, status in services_status.items() if status != "healthy"}

        if unhealthy_services:
            raise RuntimeError(f"Unhealthy services: {unhealthy_services}")

        return {
            "status": "healthy",
            "version": "1.0.0",
            "services": services_status,
        }
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {e!s}",
        ) from e
