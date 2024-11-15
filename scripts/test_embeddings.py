import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.embeddings_service import EmbeddingsService
from src.services.config_service import config_service
from google.cloud import storage
import logging

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
                "metadata": {"test": True, "category": "test"}
            },
            {
                "text": "Test document 2", 
                "metadata": {"test": True, "category": "test"}
            },
            {
                "text": "This is a completely different topic about machine learning",
                "metadata": {"test": True, "category": "ml"}
            }
        ]
        
        logger.info("Testing document addition")
        count = embeddings.add(test_docs)
        logger.info(f"Added {count} documents")
        assert count == len(test_docs)
        
        # Test simple search
        logger.info("Testing simple search functionality")
        results = embeddings.simple_search("test document", 1)
        logger.info(f"Simple search results: {results}")
        assert len(results) > 0, "Simple search returned no results"
        
        # Test hybrid search
        logger.info("Testing hybrid search functionality")
        results = embeddings.hybrid_search("machine learning", 1)
        logger.info(f"Hybrid search results: {results}")
        assert len(results) > 0, "Hybrid search returned no results"
        assert "scores" in results[0], "Hybrid search results missing scores"
        
    except Exception as e:
        logger.error(f"Embeddings test failed: {str(e)}", exc_info=True)
        assert False, f"Embeddings test failed: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting embeddings tests")
    
    # Test GCS first
    if not test_gcs_connection():
        logger.error("GCS connection test failed")
        exit(1)
        
    # Test embeddings
    if not test_embeddings():
        logger.error("Embeddings test failed")
        exit(1)
        
    logger.info("All tests passed successfully") 