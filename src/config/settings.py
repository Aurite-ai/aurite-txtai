from txtai.api import API
import logging
from typing import Dict, Any
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional, Literal
import os
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "debug"
    ENV: str = "development"

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Stream Configuration
    STREAM_BLOCK_MS: int = 5000
    STREAM_RAG: str = "rag_stream"
    STREAM_EMBEDDINGS: str = "embeddings_stream"
    STREAM_LLM: str = "llm_stream"
    STREAMS: List[str] = [STREAM_RAG, STREAM_EMBEDDINGS, STREAM_LLM]

    # Consumer Groups
    CONSUMER_GROUP_TXTAI: str = "txtai-group"
    CONSUMER_NAME_TXTAI: str = "txtai-consumer"

    # txtai Configuration
    TXTAI_HOST: str = os.getenv("TXTAI_HOST", "localhost")
    TXTAI_PORT: int = int(os.getenv("TXTAI_PORT", "8000"))
    TXTAI_URL: str = os.getenv("TXTAI_URL", f"http://{TXTAI_HOST}:{TXTAI_PORT}")

    # API Configuration
    API_KEY: str = os.getenv("API_KEY", "default-key")
    AUTH_SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "default-secret-key")

    # LLM Settings
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic")
    SYSTEM_PROMPTS: Dict[str, str] = {
        "rag": "You are a helpful AI assistant.",
        "default": "You are a helpful AI assistant.",
    }

    LLM_MODELS: Dict[str, str] = {
        "anthropic": "claude-3-5-sonnet-20240620",
        "openai": "gpt-4o-mini",
    }

    # Embeddings Settings
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/nli-mpnet-base-v2")
    EMBEDDINGS_STORAGE_TYPE: str = os.getenv("EMBEDDINGS_STORAGE_TYPE", "memory")
    EMBEDDINGS_CONTENT_PATH: str = os.getenv("EMBEDDINGS_CONTENT_PATH", ":memory:")
    EMBEDDINGS_BATCH_SIZE: int = int(os.getenv("EMBEDDINGS_BATCH_SIZE", "32"))

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
