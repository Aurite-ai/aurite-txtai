from typing import List, Dict, Any, Optional
import json
import logging
from ..config.settings import Settings, QueryType
from txtai.embeddings import Embeddings

logger = logging.getLogger(__name__)


class QueryService:
    """Service for search operations"""

    def __init__(self, embeddings: Embeddings, settings: Settings):
        self.embeddings = embeddings
        self.settings = settings

    def search(
        self,
        query: str,
        query_type: QueryType = "hybrid",
        limit: int = 10,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search using embeddings directly"""
        try:
            if query_type == "sql":
                # Format SQL query with proper indentation
                if not query.lower().startswith("select"):
                    query = f"""
                        SELECT *
                        FROM txtai
                        WHERE {query}
                    """
                results = self.embeddings.search(query)
                return self._process_sql_results(results)
            else:
                # For semantic/hybrid searches
                if metadata_filters:
                    # Build metadata filter conditions
                    conditions = [
                        f"metadata LIKE '%{json.dumps({k:v})}%'"
                        for k, v in metadata_filters.items()
                    ]
                    filter_clause = " AND ".join(conditions)

                    # Format full query
                    search_query = f"""
                        SELECT text, score, metadata
                        FROM txtai
                        WHERE {filter_clause}
                        ORDER BY similarity('{query}') DESC
                        LIMIT {limit}
                    """
                    results = self.embeddings.search(search_query)
                else:
                    results = self.embeddings.search(query, limit)
                return self._process_semantic_results(results)
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    def _process_sql_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process SQL query results"""
        processed = []
        for result in results:
            metadata = self._parse_metadata(result.get("metadata", "{}"))
            processed.append(
                {
                    "id": result.get("id", ""),
                    "text": result.get("text", ""),
                    "score": result.get("score", 1.0),
                    "metadata": metadata,
                }
            )
        return processed

    def _process_semantic_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process semantic/hybrid search results"""
        processed = []
        for result in results:
            metadata = self._parse_metadata(result.get("metadata", "{}"))
            processed.append(
                {
                    "id": result.get("id", ""),
                    "text": result.get("text", ""),
                    "score": result.get("score", 0.0),
                    "metadata": metadata,
                }
            )
        return processed

    def _parse_metadata(self, metadata: Any) -> Dict:
        """Parse metadata consistently"""
        if isinstance(metadata, str):
            try:
                return json.loads(metadata)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse metadata: {metadata}")
                return {}
        elif isinstance(metadata, dict):
            return metadata
        return {}


if __name__ == "__main__":
    import logging
    from pathlib import Path
    from ..config.settings import Settings
    from .embeddings_service import EmbeddingsService

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
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
            embeddings_service.create_index()

            logger.info("Adding test documents...")
            embeddings_service.add_documents(test_docs)

            # Create query service
            query_service = QueryService(embeddings_service.embeddings, settings)

            # Test different query types
            logger.info("\nTesting semantic search:")
            semantic_results = query_service.search(
                "machine learning", query_type="semantic", limit=1
            )
            logger.info(f"Semantic results: {json.dumps(semantic_results, indent=2)}")

            logger.info("\nTesting SQL search:")
            sql_query = """
                SELECT text, score, metadata
                FROM txtai
                WHERE metadata LIKE '%"category":"tech"%'
                ORDER BY score DESC
            """
            sql_results = query_service.search(sql_query, query_type="sql")
            logger.info(f"SQL results: {json.dumps(sql_results, indent=2)}")

            logger.info("\nTesting hybrid search with metadata filter:")
            hybrid_results = query_service.search(
                "machine learning",
                query_type="hybrid",
                limit=1,
                metadata_filters={"category": "tech"},
            )
            logger.info(f"Hybrid results: {json.dumps(hybrid_results, indent=2)}")

        except Exception as e:
            logger.error(f"Test failed: {str(e)}", exc_info=True)

    # Run the tests
    logger.info("Starting query service tests...")
    run_test_queries()
