from txtai.api import API
import logging
from typing import Dict, Any
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional, Literal


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

    # Redis Stream Names (must match persona server)
    STREAM_RAG: str = "rag_stream"
    STREAM_EMBEDDINGS: str = "embeddings_stream"
    STREAM_LLM: str = "llm_stream"

    # Redis Consumer Groups (complementary to persona server)
    CONSUMER_GROUP_TXTAI: str = "txtai-group"  # Persona uses "persona-group"
    CONSUMER_NAME_TXTAI: str = "txtai-consumer"  # Persona uses "persona-consumer"

    # Redis Stream Settings
    STREAM_READ_COUNT: int = 1
    STREAM_BLOCK_MS: int = 1000  # 1 second block

    # List of all streams for easy access
    STREAMS: List[str] = [STREAM_RAG, STREAM_EMBEDDINGS, STREAM_LLM]

    # txtai-specific settings
    EMBEDDINGS_STORAGE_TYPE: Literal["memory", "sqlite", "cloud"] = "memory"
    EMBEDDINGS_CONTENT_PATH: str = ":memory:"
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
