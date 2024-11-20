from typing import List, Dict, Any, Optional, Tuple
import logging
from txtai.embeddings import Embeddings
from src.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for managing document embeddings and search"""

    def __init__(self, settings: Settings):
        """Initialize embeddings service"""
        self.initialized = False
        self.settings = settings
        self.embeddings = None
        self.initialize()

    def initialize(self):
        """Initialize embeddings with configuration"""
        try:
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
            logger.info(f"Using config: {config}")
            self.embeddings = Embeddings(config)
            self.initialized = True
            logger.info("Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Embeddings initialization failed: {e}")
            raise

    async def add(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to embeddings index"""
        try:
            logger.info("\n=== Adding Documents ===")
            logger.info(f"Processing {len(documents)} documents")

            # Format documents for txtai
            formatted_docs = []
            for doc in documents:
                doc_id = str(doc.get("id", len(formatted_docs) + 1))
                text = doc.get("text", "")
                metadata = {k: v for k, v in doc.items() if k not in ["id", "text"]}
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
        try:
            results = self.embeddings.search(query, limit)
            return [
                {
                    "id": str(result["id"]),
                    "text": result["text"],
                    "score": result["score"],
                    **result.get("metadata", {}),
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            raise

    async def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Alias for hybrid_search to maintain compatibility"""
        return await self.hybrid_search(query, limit)
