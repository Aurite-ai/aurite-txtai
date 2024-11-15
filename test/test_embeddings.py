import os
import shutil
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.embeddings_service import EmbeddingsService
from src.services.config_service import config_service
from google.cloud import storage
import logging
import pytest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gcs_connection():
    """Test GCP authentication and bucket access"""
    try:
        logger.info("Testing GCP authentication")
        storage_client = storage.Client()
        bucket = storage_client.bucket(config_service.settings.GOOGLE_CLOUD_BUCKET)
        assert bucket.exists()
        logger.info("GCP authentication successful")
    except Exception as e:
        logger.error(f"GCP authentication failed: {str(e)}", exc_info=True)
        assert False, f"GCP authentication failed: {str(e)}"

def test_embeddings():
    """Test embeddings initialization and basic operations"""
    try:
        logger.info("Testing embeddings service initialization")
        embeddings = EmbeddingsService()
        
        # Test document addition
        test_docs = [
            {
                "text": "Test document 1", 
                "metadata": {"test": True, "category": "test", "length": 50}
            },
            {
                "text": "Test document 2", 
                "metadata": {"test": True, "category": "test", "length": 75}
            },
            {
                "text": "This is a completely different topic about machine learning",
                "metadata": {"test": True, "category": "ml", "length": 100}
            }
        ]
        
        logger.info("Testing document addition")
        count = embeddings.add(test_docs)
        logger.info(f"Added {count} documents")
        assert count == len(test_docs)
        
        # Test document count
        count = embeddings.count()
        assert count == len(test_docs), "Document count mismatch"
        
        # Test semantic search
        logger.info("Testing semantic search functionality")
        results = embeddings.semantic_search("test document", 1)
        logger.info(f"Semantic search results: {results}")
        assert len(results) > 0, "Semantic search returned no results"
        assert "metadata" in results[0], "Semantic search results missing metadata"
        
        # Test hybrid search
        logger.info("Testing hybrid search functionality")
        results = embeddings.hybrid_search("machine learning", 1)
        logger.info(f"Hybrid search results: {results}")
        assert len(results) > 0, "Hybrid search returned no results"
        assert "scores" in results[0], "Hybrid search results missing scores"
        assert "semantic" in results[0]["scores"], "Missing semantic score"
        assert "keyword" in results[0]["scores"], "Missing keyword score"
        assert "metadata" in results[0], "Hybrid search results missing metadata"
        
        # Test SQL search
        logger.info("Testing SQL search functionality")
        results = embeddings.sql_search(
            "select text, score from txtai where similar('machine learning') and score >= 0.1"
        )
        assert len(results) > 0, "SQL search returned no results"
        
        # Test save and load
        logger.info("Testing index persistence")
        test_path = "/tmp/test_index"
        embeddings.save(test_path)
        
        # Create new instance and load saved index
        new_embeddings = EmbeddingsService()
        new_embeddings.load(test_path)
        assert new_embeddings.count() == count, "Loaded index has different document count"
        
        # Cleanup
        if os.path.exists(test_path):
            shutil.rmtree(test_path)
        
    except Exception as e:
        logger.error(f"Embeddings test failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("Starting embeddings tests")
    test_gcs_connection()
    test_embeddings()
    logger.info("All tests passed successfully") 