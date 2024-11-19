from txtai.api import API
from ..config.settings import Settings
from ..config.txtai_config import create_embeddings_config, create_llm_config
from .base_service import BaseService
import logging


class ConfigService(BaseService):
    """Service for managing application configuration"""

    def __init__(self):
        super().__init__()
        self._settings = None
        self._api_config = None
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    @property
    def settings(self):
        """Get settings"""
        if not self._settings:
            self._settings = Settings()
        return self._settings

    @settings.setter
    def settings(self, value):
        """Set settings"""
        self._settings = value
        self._initialized = False

    async def initialize(self):
        """Initialize configuration service"""
        if not self.initialized:
            try:
                if not self._settings:
                    self._settings = Settings()

                self._api_config = API(
                    {
                        "embeddings": {
                            "path": self.settings.EMBEDDINGS_MODEL,
                            "content": True,
                            "backend": "faiss",
                        },
                        "token": self.settings.API_KEY,
                    }
                )
                self._initialized = True
                self.logger.info("Config service initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize config service: {e}")
                raise

    @property
    def embeddings_config(self) -> dict:
        """Get embeddings configuration"""
        self._check_initialized()
        return create_embeddings_config(self.settings)

    @property
    def llm_config(self) -> dict:
        """Get LLM configuration"""
        self._check_initialized()
        return create_llm_config(self.settings)


# Global config service instance
config_service = ConfigService()
