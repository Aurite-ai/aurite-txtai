from pathlib import Path
import json
import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

from txtai.embeddings import Embeddings

from .config_service import config_service, Settings
from ..config.txtai_config import create_embeddings_config

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service to manage txtai embeddings lifecycle"""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize service with optional settings override"""
        self.settings = settings or config_service.settings
        self.embeddings: Optional[Embeddings] = None

    async def initialize(self):
        """Initialize embeddings with config"""
        try:
            # Use config_service if no settings override
            config = (
                create_embeddings_config(self.settings)
                if hasattr(self, "settings")
                else config_service.embeddings_config
            )

            logger.info("Initializing embeddings...")
            logger.info(f"Using config: {json.dumps(config, indent=2)}")

            self.embeddings = Embeddings(config)
            # Initialize empty index
            self.embeddings.index([])
            logger.info("Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {str(e)}")
            raise

    async def add(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to embeddings index"""
        if not self.embeddings:
            await self.initialize()

        try:
            logger.info("\n=== Document Processing ===")
            logger.info(f"Input documents: {json.dumps(documents, indent=2)}")

            # Format documents for txtai indexing
            formatted_docs = []
            for doc in documents:
                doc_id = str(doc.get("id", str(uuid4())))
                metadata_str = json.dumps(doc.get("metadata", {}))
                formatted_doc = (doc_id, doc["text"], metadata_str)
                formatted_docs.append(formatted_doc)

                logger.info(f"\nDocument transformation:")
                logger.info(f"Original: {json.dumps(doc, indent=2)}")
                logger.info(f"Formatted: {formatted_doc}")

            logger.info("\n=== Pre-Indexing State ===")
            logger.info(f"Number of documents to index: {len(formatted_docs)}")

            # Index the documents
            self.embeddings.index(formatted_docs)

            # Verify indexing using SQL query
            logger.info("\n=== Post-Indexing Verification ===")
            verify_query = "SELECT id, text, tags FROM txtai"
            results = self.embeddings.search(verify_query)
            logger.info(f"Indexed documents: {json.dumps(results, indent=2)}")

            return len(formatted_docs)

        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise

    async def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search on indexed documents"""
        if not self.embeddings:
            await self.initialize()

        try:
            logger.info("\n=== Search Process ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")

            # Get semantic search results
            results = self.embeddings.search(query, limit)
            logger.info(f"Raw search results: {json.dumps(results, indent=2)}")

            # Get full documents with tags
            doc_ids = [f"'{result['id']}'" for result in results]
            if not doc_ids:
                return []

            # Create the joined doc_ids string
            doc_ids_str = ','.join(doc_ids)

            # Use triple quotes for SQL and double quotes for JSON patterns
            sql_query = f'''
                SELECT id, text, tags, score
                FROM txtai
                WHERE id IN ({doc_ids_str})
            '''
            full_docs = self.embeddings.search(sql_query)
            logger.info(f"Full documents: {json.dumps(full_docs, indent=2)}")

            # Format results with metadata from tags
            formatted_results = []
            for result in results:
                # Find matching full document
                full_doc = next((doc for doc in full_docs if doc["id"] == result["id"]), None)

                if full_doc:
                    # Parse metadata from tags
                    metadata = {}
                    if full_doc.get("tags"):
                        try:
                            metadata = json.loads(full_doc["tags"])
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse tags: {e}")

                    formatted_result = {
                        "id": result["id"],
                        "text": result["text"],
                        "score": result["score"],
                        "metadata": metadata,
                    }
                    formatted_results.append(formatted_result)

            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    async def is_empty(self) -> bool:
        """Check if embeddings index is empty"""
        if not self.embeddings:
            await self.initialize()

        try:
            # Query for any document
            results = self.embeddings.search("SELECT COUNT(*) as count FROM txtai")
            return results[0]["count"] == 0
        except Exception as e:
            logger.error(f"Failed to check if index is empty: {str(e)}")
            return True


# Global service instance
embeddings_service = EmbeddingsService()

if __name__ == "__main__":
    import logging
    from pathlib import Path

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    # Test documents matching notebook pattern
    test_docs = [
        {
            "id": "doc1",
            "text": "Machine learning models require significant computational resources",
            "metadata": {
                "category": "tech",
                "tags": ["ML", "computing"],
                "priority": 1,
            },
        },
        {
            "id": "doc2",
            "text": "Natural language processing advances with transformer models",
            "metadata": {"category": "tech", "tags": ["NLP", "ML"], "priority": 2},
        },
    ]

    def inspect_embeddings():
        """Debug function to inspect embeddings state"""
        try:
            # Create and initialize service
            service = EmbeddingsService()
            service.initialize()  # Make sure to initialize

            # Log config
            logger.info("\n=== Configuration ===")
            logger.info(
                f"Embeddings config: {json.dumps(config_service.embeddings_config, indent=2)}"
            )

            # Log initial state
            logger.info("\n=== Initial State ===")
            logger.info(f"Embeddings initialized: {service.embeddings is not None}")
            if service.embeddings:
                logger.info(f"Embeddings config: {json.dumps(service.embeddings.config, indent=2)}")

            # Add documents
            logger.info("\n=== Adding Documents ===")
            count = service.add(test_docs)
            logger.info(f"Added {count} documents")

            # Test different search types
            logger.info("\n=== Testing Search Types ===")

            # Direct SQL query
            logger.info("\nDirect SQL Query:")
            sql_results = service.embeddings.search(
                '''
                SELECT * FROM txtai
            '''
            )
            logger.info(f"SQL results: {json.dumps(sql_results, indent=2)}")

            # Metadata SQL query - Using exact JSON pattern match
            logger.info("\nMetadata SQL Query:")
            metadata_results = service.embeddings.search(
                '''
                SELECT id, text, tags
                FROM txtai
                WHERE tags LIKE '%"category": "tech"%'
                ORDER BY id
            '''
            )
            logger.info(f"Metadata results: {json.dumps(metadata_results, indent=2)}")

            # Hybrid search
            logger.info("\nHybrid Search:")
            hybrid_results = service.hybrid_search("machine learning", limit=2)
            logger.info(f"Hybrid results: {json.dumps(hybrid_results, indent=2)}")

        except Exception as e:
            logger.error(f"Inspection failed: {str(e)}", exc_info=True)

    # Run inspection
    logger.info("Starting embeddings service inspection...")
    inspect_embeddings()
