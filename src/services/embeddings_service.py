from typing import List, Dict, Any, Optional
from uuid import uuid4
import json
import logging
from txtai.embeddings import Embeddings
from .config_service import config_service
from .base_service import BaseService
from ..config.txtai_config import create_embeddings_config

logger = logging.getLogger(__name__)


class EmbeddingsService(BaseService):
    """Service to manage txtai embeddings lifecycle"""

    def __init__(self):
        super().__init__()
        self.settings = None
        self.embeddings: Optional[Embeddings] = None

    async def initialize(self):
        """Initialize embeddings with config"""
        if not self.initialized:
            try:
                self.settings = config_service.settings
                config = create_embeddings_config(self.settings)

                logger.info("\n=== Initializing Embeddings ===")
                logger.info(f"Using config: {json.dumps(config, indent=2)}")

                # Create new embeddings instance
                self.embeddings = Embeddings(config)
                self._initialized = True
                logger.info("Embeddings initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {str(e)}")
                raise

    async def add(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to embeddings index"""
        self._check_initialized()
        try:
            logger.info(f"\n=== Adding {len(documents)} Documents ===")

            # Format documents for txtai indexing
            formatted_docs = []
            for doc in documents:
                doc_id = str(doc.get("id", str(uuid4())))
                text = doc["text"]
                metadata_str = json.dumps(doc.get("metadata", {}))
                formatted_doc = (doc_id, text, metadata_str)
                formatted_docs.append(formatted_doc)
                logger.info(f"Formatted document: {formatted_doc}")

            # Index the documents
            self.embeddings.index(formatted_docs)
            logger.info("Documents indexed")

            # Verify indexing
            verify_query = "SELECT COUNT(*) as count FROM txtai"
            results = self.embeddings.search(verify_query)
            count = results[0]["count"] if results else 0
            logger.info(f"Verified document count: {count}")

            # Show sample document
            if count > 0:
                sample = self.embeddings.search("SELECT id, text, tags FROM txtai LIMIT 1")
                logger.info(f"Sample document: {sample[0]}")

            return count

        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise

    async def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search"""
        self._check_initialized()
        try:
            logger.info("\n=== Search Process ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")

            # Verify index has documents
            count_query = "SELECT COUNT(*) as count FROM txtai"
            count_result = self.embeddings.search(count_query)
            doc_count = count_result[0]["count"] if count_result else 0
            logger.info(f"Documents in index: {doc_count}")

            # Perform search
            results = self.embeddings.search(query, limit)
            logger.info(f"Raw search results: {json.dumps(results, indent=2)}")

            return results
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise


# Global service instance
embeddings_service = EmbeddingsService()
