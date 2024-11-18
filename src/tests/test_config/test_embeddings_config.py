import pytest
from src.config.txtai_config import create_embeddings_config


def test_base_config(test_settings):
    """Test base configuration matches notebook pattern"""
    config = create_embeddings_config(test_settings)

    # Check core settings
    assert config["path"] == test_settings.EMBEDDINGS_MODEL
    assert config["backend"] == "faiss"
    assert config["hybrid"] is True
    assert config["normalize"] is True
    assert config["content"] is True

    # Check scoring config
    assert "scoring" in config
    assert config["scoring"]["method"] == "bm25"
    assert config["scoring"]["terms"] is True
    assert config["scoring"]["normalize"] is True
    assert config["scoring"]["weights"] == {"hybrid": 0.7, "terms": 0.3}


def test_memory_storage_config(test_settings):
    """Test memory storage configuration"""
    test_settings.EMBEDDINGS_STORAGE_TYPE = "memory"
    config = create_embeddings_config(test_settings)

    assert config["contentpath"] == ":memory:"
    assert config["batch"] == test_settings.EMBEDDINGS_BATCH_SIZE


def test_cloud_storage_config(test_settings):
    """Test cloud storage configuration"""
    test_settings.EMBEDDINGS_STORAGE_TYPE = "cloud"
    test_settings.GOOGLE_CLOUD_BUCKET = "aurite-txtai-dev"

    config = create_embeddings_config(test_settings)

    # Cloud storage config should match notebook structure
    assert config["cloud"] == {"provider": "gcs", "container": "aurite-txtai-dev"}
    assert config["contentpath"] == "gcs://aurite-txtai-dev"
