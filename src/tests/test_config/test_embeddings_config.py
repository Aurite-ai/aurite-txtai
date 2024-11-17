import pytest
from src.config.embeddings_config import get_embeddings_config
from src.config.settings import Settings


def test_memory_config(test_settings):
    """Test memory storage configuration"""
    test_settings.EMBEDDINGS_STORAGE_TYPE = "memory"
    config = get_embeddings_config(test_settings)

    assert config["path"] == test_settings.EMBEDDINGS_MODEL
    assert config["backend"] == "faiss"
    assert config["hybrid"] == True
    assert config["normalize"] == True
    assert config["contentpath"] == ":memory:"


def test_sqlite_config(test_settings):
    """Test SQLite storage configuration"""
    test_settings.EMBEDDINGS_STORAGE_TYPE = "sqlite"
    config = get_embeddings_config(test_settings)

    assert config["contentpath"] == test_settings.EMBEDDINGS_CONTENT_PATH
    assert config["batch"] == 1000


def test_cloud_config(test_settings):
    """Test cloud storage configuration"""
    test_settings.EMBEDDINGS_STORAGE_TYPE = "cloud"
    test_settings.GOOGLE_APPLICATION_CREDENTIALS = "/path/to/creds.json"
    test_settings.GOOGLE_CLOUD_BUCKET = "test-bucket"

    config = get_embeddings_config(test_settings)
    assert config["cloud"]["provider"] == "gcs"
    assert config["cloud"]["container"] == "test-bucket"
    assert config["batch"] == 500
