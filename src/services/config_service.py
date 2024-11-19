from txtai.api import API
from ..config.settings import Settings
from ..config.txtai_config import create_embeddings_config, create_llm_config
import logging
from typing import Dict, Any


class ConfigService:
    """Service for managing application configuration"""

    def __init__(self):
        self._initialized = False
        self.settings: Settings = None
        self._embeddings_config: Dict[str, Any] = None
        self._llm_config: Dict[str, Any] = None
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    @property
    def initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized

    def _check_initialized(self):
        """Check if service is initialized and raise error if not"""
        if not self._initialized:
            raise ValueError(f"{self.__class__.__name__} not initialized")

    async def initialize(self) -> None:
        """Initialize configuration service"""
        try:
            # Create configs
            self._embeddings_config = create_embeddings_config(self.settings)
            self._llm_config = create_llm_config(self.settings)

            # Mark as initialized
            self._initialized = True
            self.logger.info("Config service initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize config service: {e}")
            raise

    @property
    def embeddings_config(self) -> Dict[str, Any]:
        """Get embeddings configuration"""
        self._check_initialized()
        return self._embeddings_config

    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        self._check_initialized()
        return self._llm_config


# Global service instance
config_service = ConfigService()
