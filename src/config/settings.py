from typing import Optional, Literal, Dict, ClassVar
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
from enum import Enum

StorageType = Literal["memory", "sqlite", "cloud"]
QueryType = Literal["sql", "semantic", "hybrid"]


class LLMProvider(str, Enum):
    """LLM provider options"""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class Settings(BaseSettings):
    """Application settings"""

    # API settings
    API_KEY: str = "test-key"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Google Cloud settings
    GOOGLE_CLOUD_PROJECT: str = "aurite-dev"
    GOOGLE_CLOUD_BUCKET: str = "aurite-txtai-dev"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # Embeddings settings
    EMBEDDINGS_MODEL: str = "sentence-transformers/nli-mpnet-base-v2"
    EMBEDDINGS_STORAGE_TYPE: str = "memory"  # memory, sqlite, cloud
    EMBEDDINGS_CONTENT_PATH: str = ":memory:"
    EMBEDDINGS_PREFIX: str = "txtai"
    EMBEDDINGS_BATCH_SIZE: int = 32

    # LLM settings
    LLM_PROVIDER: LLMProvider = LLMProvider.ANTHROPIC
    LLM_MODELS: Dict[str, str] = {
        "anthropic": "anthropic/claude-3-sonnet-20240229",
        "openai": "gpt-4-turbo-preview",
    }
    ANTHROPIC_API_KEY: str = Field(..., env="ANTHROPIC_API_KEY")
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")

    # System prompts
    SYSTEM_PROMPTS: Dict[str, str] = {
        "rag": "You are a helpful AI assistant.",
        "default": "You are a helpful AI assistant.",
    }

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # ZMQ settings
    ZMQ_BASE_PORT: int = 5555

    # Communication channels - using ClassVar since this is a static configuration
    CHANNELS: ClassVar[Dict[str, str]] = {
        "embeddings": "embeddings_stream",
        "rag": "rag_stream",
        "llm": "llm_stream",
        "agent_requests": "agent_requests",
        "agent_responses": "agent_responses",
    }

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")
