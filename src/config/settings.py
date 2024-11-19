from typing import Optional, Literal, Dict, ClassVar
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field

StorageType = Literal["memory", "sqlite", "cloud"]
QueryType = Literal["sql", "semantic", "hybrid"]
LLMProvider = Literal["anthropic", "openai"]


class Settings(BaseSettings):
    """Application runtime settings"""

    # API Settings
    API_KEY: str
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Cloud Settings
    GOOGLE_CLOUD_PROJECT: str = "aurite-dev"
    GOOGLE_CLOUD_BUCKET: str = "aurite-txtai-dev"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # Embeddings Settings
    EMBEDDINGS_MODEL: str = "sentence-transformers/nli-mpnet-base-v2"
    EMBEDDINGS_STORAGE_TYPE: StorageType = "memory"
    EMBEDDINGS_CONTENT_PATH: str = "txtai/content.db"
    EMBEDDINGS_PREFIX: str = "txtai"
    EMBEDDINGS_BATCH_SIZE: int = 32

    # LLM Settings
    LLM_PROVIDER: LLMProvider = "anthropic"
    LLM_MODELS: dict = {
        "anthropic": "anthropic/claude-3-sonnet-20240229",
        "openai": "openai/gpt-4-turbo-preview",
    }
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # System Prompts
    SYSTEM_PROMPTS: dict = {
        "default": """You are a helpful AI assistant. Answer questions clearly and concisely.""",
        "rag": """You are a helpful AI assistant. You must ONLY answer questions using the provided context.
If the answer cannot be found in the context, you must clearly state that the information is not available in the given context.""",
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
