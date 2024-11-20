from typing import List, Dict, Any, Optional
from uuid import uuid4
import json
import logging
from txtai.embeddings import Embeddings
from ..base_service import BaseService
from src.config import Settings

logger = logging.getLogger(__name__)


def create_embeddings_config(settings: Settings) -> Dict[str, Any]:
    """Create embeddings configuration"""
    config = {
        "path": settings.EMBEDDINGS_MODEL,
        "content": True,
        "backend": "faiss",
        "hybrid": True,
        "normalize": True,
        "scoring": {
            "method": "bm25",
            "terms": True,
            "normalize": True,
            "weights": {"hybrid": 0.7, "terms": 0.3},
        },
        "batch": settings.EMBEDDINGS_BATCH_SIZE,
        "contentpath": settings.EMBEDDINGS_CONTENT_PATH,
        "database": True,
        "storetokens": True,
        "storeannoy": True,
    }

    # Add cloud configuration if using cloud storage
    if settings.EMBEDDINGS_STORAGE_TYPE == "cloud":
        config["cloud"] = {
            "provider": "gcs",
            "container": settings.GOOGLE_CLOUD_BUCKET,
            "prefix": settings.EMBEDDINGS_PREFIX,
        }
        config["contentpath"] = f"gcs://{settings.GOOGLE_CLOUD_BUCKET}"

    # Use memory storage if specified
    elif settings.EMBEDDINGS_STORAGE_TYPE == "memory":
        config["contentpath"] = ":memory:"

    return config


class EmbeddingsService(BaseService):
    """Service to manage txtai embeddings lifecycle"""

    def __init__(self):
        super().__init__()
        self.settings: Optional[Settings] = None
        self.embeddings: Optional[Embeddings] = None

    async def initialize(self, settings: Settings = None):
        """Initialize embeddings with config"""
        if not self.initialized:
            try:
                self.settings = settings or Settings()
                config = create_embeddings_config(self.settings)

                logger.info("\n=== Initializing Embeddings ===")
                logger.info(f"Using config: {json.dumps(config, indent=2)}")

                # Create new embeddings instance
                self.embeddings = Embeddings(config)

                # Initialize database and create empty index
                self.embeddings.index([("init", "init", "{}")])
                self.embeddings.delete(["init"])

                self._initialized = True
                logger.info("Embeddings initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {str(e)}")
                raise

    async def add(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to embeddings index"""
        self._check_initialized()
        try:
            logger.info("\n=== Adding Documents ===")
            logger.info(f"Processing {len(documents)} documents")

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
            logger.info("Indexing documents...")
            self.embeddings.index(formatted_docs)
            logger.info("Documents indexed")

            # Verify indexing
            verify_query = "SELECT COUNT(*) as count FROM txtai"
            logger.info(f"Verifying with query: {verify_query}")
            results = self.embeddings.search(verify_query)
            count = results[0]["count"] if results else 0
            logger.info(f"Verified count: {count}")

            return count

        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise

    async def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search for documents using hybrid search by default"""
        self._check_initialized()
        try:
            logger.info(f"Searching for: {query} (limit: {limit})")

            # Format search query
            search_query = f"""
            SELECT id, text, score, tags as metadata
            FROM txtai
            WHERE similar('{query}')
            LIMIT {limit}
            """

            # Execute search
            results = self.embeddings.search(search_query)

            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    "id": result["id"],
                    "text": result["text"],
                    "score": result["score"],
                    "metadata": json.loads(result["metadata"]) if result.get("metadata") else {},
                }
                formatted_results.append(formatted_result)

            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    async def delete(self, ids: List[str]) -> None:
        """Delete documents by ID"""
        self._check_initialized()
        try:
            # Convert list to tuple for SQL IN clause
            if isinstance(ids, str):
                # If it's a SQL query, use it directly
                delete_query = ids
            else:
                # If it's a list of IDs, create IN clause
                id_tuple = tuple(ids)
                delete_query = f"DELETE FROM txtai WHERE id IN {id_tuple}"

            self.embeddings.delete(delete_query)
            logger.info(f"Deleted documents with query: {delete_query}")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise


# Global service instance
embeddings_service = EmbeddingsService()
