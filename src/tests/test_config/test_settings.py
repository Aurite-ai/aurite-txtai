from __future__ import annotations

import os

from dotenv import load_dotenv
import pytest

from src.config import Settings


# Load environment variables
load_dotenv()


@pytest.fixture
def base_settings():
    """Base settings fixture with required fields"""
    return {
        "API_KEY": "test-key",
        "EMBEDDINGS_MODEL": "sentence-transformers/nli-mpnet-base-v2",
        "EMBEDDINGS_STORAGE_TYPE": "memory",
        "EMBEDDINGS_CONTENT_PATH": ":memory:",
        "EMBEDDINGS_BATCH_SIZE": 32,
        "LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "SYSTEM_PROMPTS": {
            "rag": "You are a helpful AI assistant.",
            "default": "You are a helpful AI assistant.",
        },
    }


def test_default_settings(base_settings) -> None:
    """Test default settings match expected values"""
    settings = Settings(**base_settings)

    # Test core settings
    assert settings.EMBEDDINGS_MODEL == "sentence-transformers/nli-mpnet-base-v2"
    assert settings.EMBEDDINGS_STORAGE_TYPE == "memory"
    assert settings.API_HOST == "0.0.0.0"
    assert settings.API_PORT == 8000
    assert settings.EMBEDDINGS_BATCH_SIZE == 32
    assert settings.LLM_PROVIDER == "anthropic"


def test_storage_type_validation() -> None:
    """Test validation of storage type"""
    with pytest.raises(ValueError, match="1 validation error"):
        Settings(
            EMBEDDINGS_STORAGE_TYPE="invalid",  # Invalid storage type
            EMBEDDINGS_CONTENT_PATH=":memory:",
            API_KEY="test-key",
            EMBEDDINGS_MODEL="test-model",
            EMBEDDINGS_BATCH_SIZE=32,
            LLM_PROVIDER="anthropic",
            ANTHROPIC_API_KEY="test-key",
            SYSTEM_PROMPTS={
                "rag": "You are a helpful AI assistant.",
                "default": "You are a helpful AI assistant.",
            },
        )


def test_valid_settings() -> None:
    """Test valid settings configuration"""
    settings = Settings(
        EMBEDDINGS_STORAGE_TYPE="memory",
        EMBEDDINGS_CONTENT_PATH=":memory:",
        API_KEY="test-key",
        EMBEDDINGS_MODEL="test-model",
        EMBEDDINGS_BATCH_SIZE=32,
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="test-key",
        SYSTEM_PROMPTS={
            "rag": "You are a helpful AI assistant.",
            "default": "You are a helpful AI assistant.",
        },
    )
    assert settings.EMBEDDINGS_STORAGE_TYPE == "memory"
    assert settings.EMBEDDINGS_CONTENT_PATH == ":memory:"


def test_cloud_settings() -> None:
    """Test cloud settings validation"""
    cloud_settings = Settings(
        EMBEDDINGS_STORAGE_TYPE="cloud",
        EMBEDDINGS_CONTENT_PATH="gcs://bucket/path",
        API_KEY="test-key",
        EMBEDDINGS_MODEL="test-model",
        EMBEDDINGS_BATCH_SIZE=32,
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="test-key",
        GOOGLE_CLOUD_BUCKET="aurite-txtai-dev",
        GOOGLE_CLOUD_PROJECT="aurite-dev",
        SYSTEM_PROMPTS={
            "rag": "You are a helpful AI assistant.",
            "default": "You are a helpful AI assistant.",
        },
    )
    assert cloud_settings.GOOGLE_CLOUD_BUCKET == "aurite-txtai-dev"
    assert cloud_settings.GOOGLE_CLOUD_PROJECT == "aurite-dev"


def test_llm_settings() -> None:
    """Test LLM-specific settings"""
    settings = Settings(
        EMBEDDINGS_STORAGE_TYPE="memory",
        EMBEDDINGS_CONTENT_PATH=":memory:",
        API_KEY="test-key",
        EMBEDDINGS_MODEL="test-model",
        EMBEDDINGS_BATCH_SIZE=32,
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="test-key",
        SYSTEM_PROMPTS={
            "rag": "You are a helpful AI assistant.",
            "default": "You are a helpful AI assistant.",
        },
    )
    assert settings.LLM_PROVIDER == "anthropic"
    assert settings.ANTHROPIC_API_KEY == "test-key"
    assert "rag" in settings.SYSTEM_PROMPTS
    assert "default" in settings.SYSTEM_PROMPTS


def test_environment_override(monkeypatch, base_settings) -> None:
    """Test environment variable override"""
    monkeypatch.setenv("EMBEDDINGS_MODEL", "test-model")
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    settings = Settings()
    assert settings.EMBEDDINGS_MODEL == "test-model"
    assert settings.API_KEY == "test-key"
    assert settings.LLM_PROVIDER == "anthropic"
