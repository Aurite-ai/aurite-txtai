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


def test_storage_configs(test_settings):
    """Test storage-specific configurations"""
    # Memory storage
    test_settings.EMBEDDINGS_STORAGE_TYPE = "memory"
    memory_config = create_embeddings_config(test_settings)
    assert memory_config["contentpath"] == ":memory:"

    # SQLite storage
    test_settings.EMBEDDINGS_STORAGE_TYPE = "sqlite"
    sqlite_config = create_embeddings_config(test_settings)
    assert sqlite_config["contentpath"] == test_settings.STORAGE_PATH
    assert sqlite_config["batch"] == 1000


def test_cloud_config(test_settings):
    """Test cloud storage configuration"""
    test_settings.EMBEDDINGS_STORAGE_TYPE = "cloud"
    test_settings.GOOGLE_CLOUD_BUCKET = "test-bucket"

    config = create_embeddings_config(test_settings)
    assert config["cloud"]["provider"] == "gcs"
    assert config["cloud"]["bucket"] == "test-bucket"
    assert config["batch"] == 500
