import pytest
from src.config.txtai_config import create_embeddings_config
from src.config.settings import Settings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture
def base_settings():
    """Base settings fixture with required fields"""
    return Settings(
        API_KEY="test-key",
        EMBEDDINGS_MODEL="sentence-transformers/nli-mpnet-base-v2",
        EMBEDDINGS_STORAGE_TYPE="memory",
        EMBEDDINGS_CONTENT_PATH=":memory:",
        EMBEDDINGS_BATCH_SIZE=32,
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY"),
        SYSTEM_PROMPTS={
            "rag": "You are a helpful AI assistant.",
            "default": "You are a helpful AI assistant.",
        },
    )


def test_base_config(base_settings):
    """Test base configuration matches expected pattern"""
    config = create_embeddings_config(base_settings)

    # Check core settings
    assert config["path"] == base_settings.EMBEDDINGS_MODEL
    assert config["backend"] == "faiss"
    assert config["hybrid"] is True
    assert config["normalize"] is True
    assert config["content"] is True
    assert config["database"] is True
    assert config["storetokens"] is True
    assert config["storeannoy"] is True

    # Check scoring config
    assert "scoring" in config
    assert config["scoring"]["method"] == "bm25"
    assert config["scoring"]["terms"] is True
    assert config["scoring"]["normalize"] is True
    assert config["scoring"]["weights"] == {"hybrid": 0.7, "terms": 0.3}


def test_memory_storage_config(base_settings):
    """Test memory storage configuration"""
    base_settings.EMBEDDINGS_STORAGE_TYPE = "memory"
    config = create_embeddings_config(base_settings)

    assert config["contentpath"] == ":memory:"
    assert config["batch"] == base_settings.EMBEDDINGS_BATCH_SIZE


def test_cloud_storage_config(base_settings):
    """Test cloud storage configuration"""
    # Update settings for cloud storage
    base_settings.EMBEDDINGS_STORAGE_TYPE = "cloud"
    base_settings.GOOGLE_CLOUD_BUCKET = "aurite-txtai-dev"
    base_settings.EMBEDDINGS_PREFIX = "txtai"

    config = create_embeddings_config(base_settings)

    # Cloud storage config should match expected structure
    assert config["cloud"] == {
        "provider": "gcs",
        "container": "aurite-txtai-dev",
        "prefix": "txtai",
    }
    assert config["contentpath"] == "gcs://aurite-txtai-dev"


def test_batch_size_config(base_settings):
    """Test batch size configuration"""
    base_settings.EMBEDDINGS_BATCH_SIZE = 64
    config = create_embeddings_config(base_settings)

    assert config["batch"] == 64


def test_model_config(base_settings):
    """Test model configuration"""
    base_settings.EMBEDDINGS_MODEL = "alternative-model"
    config = create_embeddings_config(base_settings)

    assert config["path"] == "alternative-model"
