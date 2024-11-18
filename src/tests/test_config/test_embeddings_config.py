import pytest
from src.config.txtai_config import create_embeddings_config


def test_base_config(test_settings):
    """Test base configuration matches notebook pattern"""
    config = create_embeddings_config(test_settings)

    # Check core settings from notebook
    assert config["path"] == test_settings.EMBEDDINGS_MODEL
    assert config["backend"] == "faiss"
    assert config["hybrid"] is True
    assert config["normalize"] is True
    assert "scoring" in config
    assert config["scoring"]["method"] == "bm25"


def test_storage_configs(test_settings):
    """Test storage-specific configurations"""
    # Memory storage
    test_settings.EMBEDDINGS_STORAGE_TYPE = "memory"
    memory_config = create_embeddings_config(test_settings)
    assert memory_config.get("contentpath") == ":memory:"

    # SQLite storage
    test_settings.EMBEDDINGS_STORAGE_TYPE = "sqlite"
    sqlite_config = create_embeddings_config(test_settings)
    assert sqlite_config["contentpath"] == test_settings.EMBEDDINGS_CONTENT_PATH
    assert sqlite_config["batch"] == test_settings.EMBEDDINGS_BATCH_SIZE


def test_cloud_config(test_settings):
    """Test cloud storage configuration"""
    test_settings.EMBEDDINGS_STORAGE_TYPE = "cloud"
    test_settings.GOOGLE_CLOUD_BUCKET = "test-bucket"

    config = create_embeddings_config(test_settings)
    assert config["cloud"]["provider"] == "gcs"
    assert config["cloud"]["container"] == "test-bucket"
    assert config["batch"] == test_settings.EMBEDDINGS_BATCH_SIZE


def test_scoring_config(test_settings):
    """Test scoring configuration"""
    config = create_embeddings_config(test_settings)

    assert config["scoring"]["method"] == "bm25"
    assert config["scoring"]["terms"] is True
    assert config["scoring"]["normalize"] is True


def test_content_settings(test_settings):
    """Test content-related settings"""
    config = create_embeddings_config(test_settings)

    assert config["content"] is True  # Content storage should be enabled
    assert config["normalize"] is True  # Vector normalization should be enabled
    assert config["hybrid"] is True  # Hybrid search should be enabled
