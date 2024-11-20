from typing import List, Dict, Any, Optional
import json
import logging
from txtai.embeddings import Embeddings
from src.config import Settings
from ..base_service import BaseService

logger = logging.getLogger(__name__)


class EmbeddingsService(BaseService):
    """Service for managing document embeddings and search"""

    def __init__(self):
        """Initialize embeddings service"""
        super().__init__()
        self.settings = None
        self.embeddings = None

    async def initialize(self, settings: Settings) -> None:
        """Initialize embeddings with configuration"""
        if not self.initialized:
            try:
                self.settings = settings
                logger.info("\n=== Initializing Embeddings ===")
                config = {
                    "path": self.settings.EMBEDDINGS_MODEL,
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
                    "batch": self.settings.EMBEDDINGS_BATCH_SIZE,
                    "contentpath": self.settings.EMBEDDINGS_CONTENT_PATH,
                    "database": True,
                    "storetokens": True,
                    "storeannoy": True,
                }
                logger.info(f"Using config: {json.dumps(config, indent=2)}")

                # Create embeddings instance
                self.embeddings = Embeddings(config)

                # Initialize database and create empty index
                self.embeddings.index([("init", "init", "{}")])
                self.embeddings.delete(["init"])

                self._initialized = True
                logger.info("Embeddings initialized successfully")
            except Exception as e:
                logger.error(f"Embeddings initialization failed: {e}")
                raise

    async def add(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to embeddings index"""
        self._check_initialized()
        try:
            logger.info("\n=== Adding Documents ===")
            logger.info(f"Processing {len(documents)} documents")

            # Format documents for txtai
            formatted_docs = []
            for doc in documents:
                doc_id = str(doc.get("id", len(formatted_docs) + 1))
                text = doc.get("text", "")
                metadata = json.dumps({k: v for k, v in doc.items() if k not in ["id", "text"]})
                formatted = (doc_id, text, metadata)
                logger.info(f"Formatted document: {formatted}")
                formatted_docs.append(formatted)

            logger.info("Indexing documents...")
            self.embeddings.index(formatted_docs)
            logger.info("Documents indexed")

            # Verify count
            logger.info("Verifying with query: SELECT COUNT(*) as count FROM txtai")
            count = self.embeddings.search("SELECT COUNT(*) as count FROM txtai")[0]["count"]
            logger.info(f"Verified count: {count}")
            return count

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    async def hybrid_search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Perform hybrid search (semantic + keyword) on indexed documents"""
        self._check_initialized()
        try:
            # Format search query with hybrid scoring
            search_query = f"""
            SELECT id, text, score, tags as metadata
            FROM txtai
            WHERE similar('{query}')
            LIMIT {limit}
            """

            results = self.embeddings.search(search_query)
            return [
                {
                    "id": str(result["id"]),
                    "text": result["text"],
                    "score": result["score"],
                    "metadata": json.loads(result["metadata"]) if result.get("metadata") else {},
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            raise

    async def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Alias for hybrid_search to maintain compatibility"""
        return await self.hybrid_search(query, limit)


# Global service instance
embeddings_service = EmbeddingsService()
