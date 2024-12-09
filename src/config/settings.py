from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000  # txtai service port
    LOG_LEVEL: str = "debug"
    ENV: str = "development"

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    # Stream Configuration
    STREAM_BLOCK_MS: int = 5000
    STREAM_READ_COUNT: int = 100

    # Stream Names
    STREAM_PREFIX: str = "stream"
    STREAM_RAG: str = f"rag_{STREAM_PREFIX}"
    STREAM_EMBEDDINGS: str = f"embeddings_{STREAM_PREFIX}"
    STREAM_LLM: str = f"llm_{STREAM_PREFIX}"
    STREAMS: list[str] = [STREAM_RAG, STREAM_EMBEDDINGS, STREAM_LLM]

    # Consumer Configuration
    CONSUMER_PREFIX: str = "txtai"
    CONSUMER_GROUP_TXTAI: str = f"{CONSUMER_PREFIX}_group"
    CONSUMER_NAME_TXTAI: str = f"{CONSUMER_PREFIX}_consumer"

    # Message Types and Stream Mapping
    MESSAGE_TYPES: dict[str, str] = {
        "rag_request": STREAM_RAG,
        "rag_response": STREAM_RAG,
        "embeddings_request": STREAM_EMBEDDINGS,
        "embeddings_response": STREAM_EMBEDDINGS,
        "llm_request": STREAM_LLM,
        "llm_response": STREAM_LLM,
    }

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
    SYSTEM_PROMPTS: dict[str, str] = {
        "rag": "You are a helpful AI assistant.",
        "default": "You are a helpful AI assistant.",
    }
    LLM_MODELS: dict[str, str] = {
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


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
