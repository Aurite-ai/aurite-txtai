import pytest
from src.config.settings import Settings


def test_default_settings():
    """Test default settings values"""
    settings = Settings()
    assert settings.EMBEDDINGS_MODEL == "sentence-transformers/nli-mpnet-base-v2"
    assert settings.EMBEDDINGS_STORAGE_TYPE == "memory"
    assert settings.EMBEDDINGS_CONTENT_PATH == "txtai/content.db"
    assert settings.EMBEDDINGS_PREFIX == "txtai"
    assert settings.has_cloud_credentials == False


def test_cloud_credentials_validation():
    """Test cloud credentials validation property"""
    # Test with credentials
    settings = Settings(
        GOOGLE_APPLICATION_CREDENTIALS="/path/to/creds.json",
        GOOGLE_CLOUD_PROJECT="test-project",
        GOOGLE_CLOUD_BUCKET="test-bucket",
    )
    assert settings.has_cloud_credentials == True

    # Test without credentials
    settings = Settings()
    assert settings.has_cloud_credentials == False


def test_custom_settings():
    """Test custom settings override defaults"""
    custom_settings = Settings(
        EMBEDDINGS_MODEL="different-model",
        EMBEDDINGS_STORAGE_TYPE="sqlite",
        EMBEDDINGS_CONTENT_PATH="custom/path.db",
        EMBEDDINGS_PREFIX="custom",
    )
    assert custom_settings.EMBEDDINGS_MODEL == "different-model"
    assert custom_settings.EMBEDDINGS_STORAGE_TYPE == "sqlite"
    assert custom_settings.EMBEDDINGS_CONTENT_PATH == "custom/path.db"
    assert custom_settings.EMBEDDINGS_PREFIX == "custom"


def test_invalid_storage_type():
    """Test setting invalid storage type"""
    with pytest.raises(ValueError):
        Settings(EMBEDDINGS_STORAGE_TYPE="invalid")
