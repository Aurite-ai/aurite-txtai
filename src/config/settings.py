from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional, Literal, Dict


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_KEY: str = "txtai-api-key"

    # Redis Connection Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0

    # Redis Stream Names
    STREAM_RAG: str = "rag_stream"
    STREAM_EMBEDDINGS: str = "embeddings_stream"
    STREAM_LLM: str = "llm_stream"

    # Redis Consumer Groups
    CONSUMER_GROUP_TXTAI: str = "txtai-group"
    CONSUMER_NAME_TXTAI: str = "txtai-consumer"

    # Redis Stream Settings
    STREAM_READ_COUNT: int = 1
    STREAM_BLOCK_MS: int = 1000  # 1 second block

    # List of all streams for easy access
    STREAMS: List[str] = [STREAM_RAG, STREAM_EMBEDDINGS, STREAM_LLM]

    # Storage types
    EMBEDDINGS_STORAGE_TYPE: Literal["memory", "sqlite", "cloud"]
    EMBEDDINGS_CONTENT_PATH: str
    EMBEDDINGS_PREFIX: str = "txtai"
    EMBEDDINGS_BATCH_SIZE: int = 32
    EMBEDDINGS_MODEL: str = "sentence-transformers/nli-mpnet-base-v2"

    # LLM settings
    LLM_PROVIDER: Literal["anthropic", "openai"] = "anthropic"
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODELS: Dict[str, str] = {
        "anthropic": "claude-3-sonnet-20240229",
        "openai": "gpt-4-turbo-preview",
    }

    # System Prompts
    SYSTEM_PROMPTS: Dict[str, str] = {
        "rag": "You are a helpful AI assistant.",
        "default": "You are a helpful AI assistant.",
    }

    # Cloud settings
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_BUCKET: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
