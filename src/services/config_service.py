from txtai.api import API
from ..config.settings import Settings
from ..config.txtai_config import create_embeddings_config, create_llm_config


class ConfigService:
    """Service for managing application configuration"""

    def __init__(self):
        self.settings = Settings()
        self._api_config = None
        self.initialize_api()

    def initialize_api(self):
        """Initialize the txtai API configuration"""
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

    @property
    def embeddings_config(self) -> dict:
        """Get embeddings configuration"""
        return create_embeddings_config(self.settings)

    @property
    def llm_config(self) -> dict:
        """Get LLM configuration"""
        return create_llm_config(self.settings)


# Global config service instance
config_service = ConfigService()
