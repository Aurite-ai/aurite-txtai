from typing import List, Dict, Any, Optional
import json
import logging
from ..config.settings import Settings, QueryType
from txtai.embeddings import Embeddings

logger = logging.getLogger(__name__)


class QueryService:
    """Service for handling different types of txtai searches"""

    def __init__(self, embeddings: Embeddings, settings: Settings):
        """Initialize with embeddings instance and settings"""
        self.embeddings = embeddings
        self.settings = settings

    def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings

        Args:
            query: Search query text
            limit: Maximum number of results to return

        Returns:
            List of results with scores and metadata
        """
        try:
            logger.info("\n=== Semantic Search ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")

            # Get semantic search results
            results = self.embeddings.search(query, limit)
            logger.info(f"Raw results: {json.dumps(results, indent=2)}")

            # Get full documents with metadata
            doc_ids = [f"'{result['id']}'" for result in results]
            if not doc_ids:
                return []

            # Get complete documents with metadata
            sql_query = f'''
                SELECT id, text, tags
                FROM txtai
                WHERE id IN ({','.join(doc_ids)})
            '''
            full_docs = self.embeddings.search(sql_query)
            logger.info(f"Full documents: {json.dumps(full_docs, indent=2)}")

            # Format results
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
            logger.error(f"Semantic search failed: {str(e)}")
            raise

    def sql_search(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query on embeddings index

        Args:
            query: SQL query string

        Returns:
            List of results with metadata
        """
        try:
            logger.info("\n=== SQL Search ===")
            logger.info(f"Query: {query}")

            # Execute SQL query
            results = self.embeddings.search(query)
            logger.info(f"Raw results: {json.dumps(results, indent=2)}")

            # Format results
            formatted_results = []
            for result in results:
                # Parse metadata from tags if present
                metadata = {}
                if result.get("tags"):
                    try:
                        metadata = json.loads(result["tags"])
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse tags: {e}")

                formatted_result = {
                    "id": result["id"],
                    "text": result["text"],
                    "metadata": metadata,
                }

                # Include score if present
                if "score" in result:
                    formatted_result["score"] = result["score"]

                formatted_results.append(formatted_result)

            return formatted_results

        except Exception as e:
            logger.error(f"SQL search failed: {str(e)}")
            raise

    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and term-based scoring"""
        try:
            logger.info("\n=== Hybrid Search ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")

            # Use default search which is hybrid mode from config
            results = self.embeddings.search(query, limit)
            logger.info(f"Raw results: {json.dumps(results, indent=2)}")

            # Get full documents with metadata
            doc_ids = [f"'{result['id']}'" for result in results]
            if not doc_ids:
                return []

            # Get complete documents with metadata
            sql_query = f'''
                SELECT id, text, tags
                FROM txtai
                WHERE id IN ({','.join(doc_ids)})
            '''
            full_docs = self.embeddings.search(sql_query)
            logger.info(f"Full documents: {json.dumps(full_docs, indent=2)}")

            # Format results
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
            logger.error(f"Hybrid search failed: {str(e)}")
            raise


if __name__ == "__main__":
    import logging
    from pathlib import Path
    from ..config.settings import Settings
    from .embeddings_service import EmbeddingsService

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

    def run_test_queries():
        """Run test queries to demonstrate functionality"""
        try:
            # Initialize services
            settings = Settings(
                EMBEDDINGS_STORAGE_TYPE="memory", EMBEDDINGS_CONTENT_PATH=":memory:"
            )

            logger.info("Creating embeddings service...")
            embeddings_service = EmbeddingsService(settings)
            logger.info("Initializing embeddings...")
            embeddings_service.initialize()

            logger.info("Adding test documents...")
            embeddings_service.add(test_docs)

            # Create query service
            query_service = QueryService(embeddings_service.embeddings, settings)

            # Test different query types
            logger.info("\nTesting semantic search:")
            semantic_results = query_service.semantic_search("machine learning", limit=1)
            logger.info(f"Semantic results: {json.dumps(semantic_results, indent=2)}")

            logger.info("\nTesting SQL search:")
            sql_query = """
                SELECT id, text, tags
                FROM txtai
                WHERE tags LIKE '%"category": "tech"%'
            """
            sql_results = query_service.sql_search(sql_query)
            logger.info(f"SQL results: {json.dumps(sql_results, indent=2)}")

            logger.info("\nTesting hybrid search:")
            hybrid_results = query_service.hybrid_search("machine learning", limit=1)
            logger.info(f"Hybrid results: {json.dumps(hybrid_results, indent=2)}")

        except Exception as e:
            logger.error(f"Test failed: {str(e)}", exc_info=True)

    # Run the tests
    logger.info("Starting query service tests...")
    run_test_queries()
