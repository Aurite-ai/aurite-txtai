import pytest
from src.config.settings import Settings


def test_default_settings():
    """Test default settings match expected values"""
    settings = Settings(API_KEY="test-key")  # API key is required

    # Test core settings
    assert settings.EMBEDDINGS_MODEL == "sentence-transformers/nli-mpnet-base-v2"
    assert settings.EMBEDDINGS_STORAGE_TYPE == "memory"
    assert settings.STORAGE_PATH == "txtai/content.db"

    # Test API settings
    assert settings.API_HOST == "0.0.0.0"
    assert settings.API_PORT == 8000

    # Test batch settings
    assert settings.EMBEDDINGS_BATCH_SIZE == 32


def test_storage_type_validation():
    """Test storage type validation"""
    with pytest.raises(ValueError):
        Settings(EMBEDDINGS_STORAGE_TYPE="invalid", API_KEY="test-key")


def test_cloud_settings():
    """Test cloud settings validation"""
    settings = Settings(
        EMBEDDINGS_STORAGE_TYPE="cloud",
        GOOGLE_CLOUD_BUCKET="test-bucket",
        GOOGLE_APPLICATION_CREDENTIALS="/path/to/creds.json",
        API_KEY="test-key",
    )
    assert settings.GOOGLE_CLOUD_BUCKET == "test-bucket"
    assert settings.GOOGLE_APPLICATION_CREDENTIALS == "/path/to/creds.json"


def test_environment_override(monkeypatch):
    """Test environment variable override"""
    monkeypatch.setenv("EMBEDDINGS_MODEL", "test-model")
    monkeypatch.setenv("API_KEY", "test-key")

    settings = Settings()
    assert settings.EMBEDDINGS_MODEL == "test-model"


def test_extra_fields_handling():
    """Test handling of extra fields in settings"""
    settings = Settings(
        API_KEY="test-key",
        PYTHONPATH="/some/path",  # Should be ignored without error
        EXTRA_SETTING="value",  # Should be ignored without error
    )
    assert settings.API_KEY == "test-key"  # Required field should work
