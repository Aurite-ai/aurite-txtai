"""Test embeddings configuration generation"""

from __future__ import annotations

import os

from dotenv import load_dotenv
import pytest

from src.config import Settings
from src.services.core.embeddings_service import create_embeddings_config


# Load environment variables
load_dotenv()


@pytest.fixture
def common_test_settings() -> dict[str, str | dict[str, str]]:
    """Common test settings fixture"""
    return {
        "API_KEY": "test-key",
        "LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "SYSTEM_PROMPTS": {
            "rag": "You are a helpful AI assistant.",
            "default": "You are a helpful AI assistant.",
        },
    }


@pytest.fixture
def base_settings(common_test_settings: dict[str, str | dict[str, str]]) -> Settings:
    """Base settings for embeddings tests"""
    return Settings(
        EMBEDDINGS_STORAGE_TYPE="memory",
        EMBEDDINGS_CONTENT_PATH=":memory:",
        EMBEDDINGS_MODEL="sentence-transformers/nli-mpnet-base-v2",
        EMBEDDINGS_BATCH_SIZE=32,
        **common_test_settings,
    )


def test_base_config(base_settings: Settings) -> None:
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

    # Check batch size
    assert config["batch"] == base_settings.EMBEDDINGS_BATCH_SIZE


def test_memory_storage_config(base_settings: Settings) -> None:
    """Test memory storage configuration"""
    base_settings.EMBEDDINGS_STORAGE_TYPE = "memory"
    config = create_embeddings_config(base_settings)

    assert config["contentpath"] == ":memory:"
    assert "cloud" not in config


def test_cloud_storage_config(base_settings: Settings) -> None:
    """Test cloud storage configuration"""
    # Update settings for cloud storage
    base_settings.EMBEDDINGS_STORAGE_TYPE = "cloud"
    base_settings.GOOGLE_CLOUD_BUCKET = "aurite-txtai-dev"
    base_settings.EMBEDDINGS_PREFIX = "txtai"

    config = create_embeddings_config(base_settings)

    # Check cloud storage config
    assert config["cloud"] == {
        "provider": "gcs",
        "container": "aurite-txtai-dev",
        "prefix": "txtai",
    }
    assert config["contentpath"] == "gcs://aurite-txtai-dev"


def test_batch_size_config(base_settings: Settings) -> None:
    """Test batch size configuration"""
    # Test default batch size
    config = create_embeddings_config(base_settings)
    assert config["batch"] == base_settings.EMBEDDINGS_BATCH_SIZE

    # Test custom batch size
    base_settings.EMBEDDINGS_BATCH_SIZE = 64
    config = create_embeddings_config(base_settings)
    assert config["batch"] == 64


def test_model_config(base_settings: Settings) -> None:
    """Test model configuration"""
    # Test default model
    config = create_embeddings_config(base_settings)
    assert config["path"] == base_settings.EMBEDDINGS_MODEL

    # Test custom model
    base_settings.EMBEDDINGS_MODEL = "alternative-model"
    config = create_embeddings_config(base_settings)
    assert config["path"] == "alternative-model"


def test_scoring_config(base_settings: Settings) -> None:
    """Test scoring configuration"""
    config = create_embeddings_config(base_settings)

    # Check scoring method
    assert config["scoring"]["method"] == "bm25"
    assert config["scoring"]["terms"] is True
    assert config["scoring"]["normalize"] is True

    # Check weights
    weights = config["scoring"]["weights"]
    assert isinstance(weights, dict)
    assert weights["hybrid"] + weights["terms"] == 1.0
    assert 0 <= weights["hybrid"] <= 1.0
    assert 0 <= weights["terms"] <= 1.0


def test_config_type_validation(base_settings: Settings) -> None:
    """Test configuration type validation"""
    config = create_embeddings_config(base_settings)

    # Validate config is correct type
    assert isinstance(config, dict)

    # Validate required fields and their types
    required_fields = {
        "path": str,
        "content": bool,
        "backend": str,
        "hybrid": bool,
        "normalize": bool,
        "scoring": dict,
        "batch": int,
        "contentpath": str,
    }

    for field, expected_type in required_fields.items():
        assert field in config, f"Missing required field: {field}"
        assert isinstance(
            config[field], expected_type
        ), f"Invalid type for {field}: expected {expected_type}, got {type(config[field])}"

    # Validate scoring config
    scoring = config["scoring"]
    assert isinstance(scoring["method"], str)
    assert isinstance(scoring["terms"], bool)
    assert isinstance(scoring["normalize"], bool)
    assert isinstance(scoring["weights"], dict)

    # Validate cloud config if present
    if "cloud" in config:
        cloud = config["cloud"]
        assert isinstance(cloud, dict)
        assert "provider" in cloud
        assert "container" in cloud
        assert "prefix" in cloud
        assert all(isinstance(v, str) for v in cloud.values())
