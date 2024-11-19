import pytest
import os
from src.config.settings import Settings
from dotenv import load_dotenv

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


def test_default_settings(base_settings):
    """Test default settings match expected values"""
    settings = Settings(**base_settings)

    # Test core settings
    assert settings.EMBEDDINGS_MODEL == "sentence-transformers/nli-mpnet-base-v2"
    assert settings.EMBEDDINGS_STORAGE_TYPE == "memory"
    assert settings.API_HOST == "0.0.0.0"
    assert settings.API_PORT == 8000
    assert settings.EMBEDDINGS_BATCH_SIZE == 32
    assert settings.LLM_PROVIDER == "anthropic"


def test_storage_type_validation(base_settings):
    """Test storage type validation"""
    invalid_settings = base_settings.copy()
    invalid_settings["EMBEDDINGS_STORAGE_TYPE"] = "invalid"

    with pytest.raises(ValueError):
        Settings(**invalid_settings)


def test_cloud_settings(base_settings):
    """Test cloud settings validation"""
    cloud_settings = base_settings.copy()
    cloud_settings.update(
        {
            "EMBEDDINGS_STORAGE_TYPE": "cloud",
            "GOOGLE_CLOUD_BUCKET": "aurite-txtai-dev",
            "GOOGLE_CLOUD_PROJECT": "aurite-dev",
        }
    )

    settings = Settings(**cloud_settings)
    assert settings.GOOGLE_CLOUD_BUCKET == "aurite-txtai-dev"
    assert settings.GOOGLE_CLOUD_PROJECT == "aurite-dev"


def test_environment_override(monkeypatch, base_settings):
    """Test environment variable override"""
    monkeypatch.setenv("EMBEDDINGS_MODEL", "test-model")
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "test-provider")

    settings = Settings()
    assert settings.EMBEDDINGS_MODEL == "test-model"
    assert settings.API_KEY == "test-key"
    assert settings.LLM_PROVIDER == "test-provider"


def test_llm_settings(base_settings):
    """Test LLM-specific settings"""
    settings = Settings(**base_settings)

    assert settings.LLM_PROVIDER == "anthropic"
    assert settings.ANTHROPIC_API_KEY == os.getenv("ANTHROPIC_API_KEY")
    assert "rag" in settings.SYSTEM_PROMPTS
    assert "default" in settings.SYSTEM_PROMPTS
