from typing import List, Dict, Any
import json
import logging
from ..config.settings import Settings, QueryType
from txtai.embeddings import Embeddings
from .base_service import BaseService

logger = logging.getLogger(__name__)


class QueryService(BaseService):
    """Service for handling different types of txtai searches"""

    def __init__(self, embeddings: Embeddings, settings: Settings):
        super().__init__()
        self.embeddings = embeddings
        self.settings = settings
        self._initialized = True  # Initialized on construction since dependencies are passed in

    async def initialize(self):
        """Initialize query service"""
        if not self.initialized:
            if not self.embeddings or not self.settings:
                raise ValueError("QueryService requires embeddings and settings")
            self._initialized = True
            logger.info("Query service initialized successfully")

    async def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        self._check_initialized()
        try:
            logger.info("\n=== Semantic Search ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")

            results = self.embeddings.search(query, limit)
            logger.info(f"Raw results: {json.dumps(results, indent=2)}")

            return await self._format_results(results)
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            raise

    async def sql_search(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query on embeddings index"""
        self._check_initialized()
        try:
            logger.info("\n=== SQL Search ===")
            logger.info(f"Query: {query}")

            results = self.embeddings.search(query)
            logger.info(f"Raw results: {json.dumps(results, indent=2)}")

            return await self._format_results(results)
        except Exception as e:
            logger.error(f"SQL search failed: {str(e)}")
            raise

    async def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and term-based scoring"""
        self._check_initialized()
        try:
            logger.info("\n=== Hybrid Search ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")

            results = self.embeddings.search(query, limit)
            logger.info(f"Raw results: {json.dumps(results, indent=2)}")

            return await self._format_results(results)
        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}")
            raise

    async def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format search results with metadata"""
        formatted_results = []
        for result in results:
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
            if "score" in result:
                formatted_result["score"] = result["score"]
            formatted_results.append(formatted_result)

        return formatted_results


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
