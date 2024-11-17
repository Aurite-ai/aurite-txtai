import pytest
from pathlib import Path
from src.services.embeddings_service import EmbeddingsService
from src.config.settings import Settings


def test_create_memory_index(test_settings, test_documents):
    """Test creating memory index and adding documents"""
    service = EmbeddingsService(test_settings)
    service.create_index("memory")
    service.add_documents(test_documents)


def test_create_sqlite_index(test_settings, test_documents, tmp_path):
    """Test creating SQLite index and adding documents"""
    service = EmbeddingsService(test_settings)
    db_path = tmp_path / "content.db"
    service.create_index("sqlite", str(db_path))
    service.add_documents(test_documents)


def test_save_load_index(test_settings, test_documents, tmp_path):
    """Test saving and loading index"""
    service = EmbeddingsService(test_settings)
    service.create_index("memory")
    service.add_documents(test_documents)

    # Save index
    save_path = tmp_path / "test_index"
    service.save_index(str(save_path))

    # Create new service and load index
    new_service = EmbeddingsService(test_settings)
    new_service.create_index("memory")
    new_service.load_index(str(save_path))


def test_invalid_storage_type(test_settings):
    """Test invalid storage type raises error"""
    service = EmbeddingsService(test_settings)
    with pytest.raises(ValueError, match="Invalid storage type"):
        service.create_index("invalid")


def test_add_documents_without_index(test_settings, test_documents):
    """Test adding documents without creating index first"""
    service = EmbeddingsService(test_settings)
    with pytest.raises(ValueError, match="No embeddings index created"):
        service.add_documents(test_documents)
