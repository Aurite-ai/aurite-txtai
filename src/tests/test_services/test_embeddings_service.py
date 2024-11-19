import pytest
import json
import logging
from src.services.embeddings_service import embeddings_service
from src.config.settings import Settings

logger = logging.getLogger(__name__)


class TestEmbeddingsCore:
    """Test embeddings core functionality"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, test_settings):
        """Test service initialization and configuration"""
        await embeddings_service.initialize()

        # Verify service configuration
        assert embeddings_service.settings == test_settings
        assert embeddings_service.embeddings is not None
        assert embeddings_service.embeddings.config["path"] == test_settings.EMBEDDINGS_MODEL
        assert embeddings_service.embeddings.config["contentpath"] == ":memory:"

    @pytest.mark.asyncio
    async def test_empty_metadata_handling(self, test_settings):
        """Test handling of documents with missing metadata"""
        await embeddings_service.initialize()

        # Document with minimal metadata
        minimal_docs = [
            {"id": "doc3", "text": "Test document with minimal metadata", "metadata": {}}
        ]

        # Should handle empty metadata without error
        count = await embeddings_service.add(minimal_docs)
        assert count == 1

        # Verify storage
        results = embeddings_service.embeddings.search("SELECT * FROM txtai")
        assert len(results) == 1
        assert json.loads(results[0]["tags"]) == {}

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in service operations"""
        # Reset service state
        embeddings_service.embeddings = None
        embeddings_service._initialized = False

        # Test operations without initialization
        with pytest.raises(ValueError, match="Embeddings not initialized"):
            await embeddings_service.add([])

        with pytest.raises(ValueError, match="Embeddings not initialized"):
            await embeddings_service.hybrid_search("test")

        # Test invalid document format
        await embeddings_service.initialize()
        with pytest.raises(KeyError):
            await embeddings_service.add([{"invalid": "document"}])
