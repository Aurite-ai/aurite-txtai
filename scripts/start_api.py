import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.config_service import config_service
import uvicorn
import logging

logger = logging.getLogger(__name__)

def main():
    """Start the API server"""
    try:
        logger.info(f"Starting txtai service on {config_service.settings.API_HOST}:{config_service.settings.API_PORT}")
        uvicorn.run(
            "src.main:app",
            host=config_service.settings.API_HOST,
            port=config_service.settings.API_PORT,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start API: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
