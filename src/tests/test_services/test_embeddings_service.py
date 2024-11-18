import pytest
from pathlib import Path
from src.services.embeddings_service import EmbeddingsService


class TestEmbeddingsStorage:
    """Test embeddings storage operations"""

    def test_memory_storage(self, test_settings, test_documents):
        """Test memory storage operations"""
        service = EmbeddingsService(test_settings)
        service.create_index("memory")
        service.add_documents(test_documents)
        assert service.embeddings is not None

    def test_persistence(self, test_settings, test_documents, tmp_path):
        """Test index persistence operations"""
        service = EmbeddingsService(test_settings)
        service.create_index("memory")
        service.add_documents(test_documents)

        # Save and load
        save_path = tmp_path / "test_index"
        service.save_index(str(save_path))

        new_service = EmbeddingsService(test_settings)
        new_service.create_index("memory")
        new_service.load_index(str(save_path))

    def test_error_handling(self, test_settings):
        """Test error handling"""
        service = EmbeddingsService(test_settings)

        # Test operations without index
        with pytest.raises(ValueError, match="No embeddings index created"):
            service.add_documents([])

        with pytest.raises(ValueError, match="No embeddings index created"):
            service.save_index("test")
