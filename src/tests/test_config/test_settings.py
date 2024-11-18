import pytest
from src.config.settings import Settings, StorageType


def test_default_settings():
    """Test default settings match notebook configuration"""
    settings = Settings()
    assert settings.EMBEDDINGS_MODEL == "sentence-transformers/nli-mpnet-base-v2"
    assert settings.EMBEDDINGS_STORAGE_TYPE == "memory"
    assert settings.STORAGE_PATH == "txtai/content.db"


def test_storage_type_validation():
    """Test storage type validation"""
    with pytest.raises(ValueError):
        Settings(EMBEDDINGS_STORAGE_TYPE="invalid")


def test_cloud_settings():
    """Test cloud settings validation"""
    settings = Settings(
        EMBEDDINGS_STORAGE_TYPE="cloud",
        GOOGLE_CLOUD_BUCKET="test-bucket",
        GOOGLE_APPLICATION_CREDENTIALS="/path/to/creds.json",
    )
    assert settings.GOOGLE_CLOUD_BUCKET == "test-bucket"
