from typing import List, Dict, Any, Optional
import json
import logging
from ..config.settings import Settings, QueryType
from .embeddings_service import EmbeddingsService

logger = logging.getLogger(__name__)


class QueryService:
    """Service to manage search operations using embeddings service

    Based on patterns from embeddings notebooks (04_Embeddings_Usage)
    """

    def __init__(self, embeddings_service: EmbeddingsService):
        """Initialize query service with embeddings service

        Args:
            embeddings_service: Configured embeddings service instance
        """
        self.embeddings = embeddings_service
        self.settings = embeddings_service.settings

    def search(
        self,
        query: str,
        query_type: QueryType = None,
        limit: int = 10,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Route search to appropriate method based on type

        Args:
            query: Search query string
            query_type: Type of search to perform ("sql", "semantic", "hybrid")
            limit: Maximum number of results to return
            metadata_filters: Optional filters to apply to metadata fields

        Returns:
            List of search results with standardized format

        Raises:
            ValueError: If embeddings index not created or invalid query type
        """
        if not self.embeddings._embeddings:
            raise ValueError("No embeddings index created. Call create_index() first")

        # Use settings default if query_type not specified
        if query_type is None:
            query_type = self.settings.DEFAULT_QUERY_TYPE

        # Route to appropriate search method
        if query_type == "sql":
            results = self.sql_search(query, limit, metadata_filters)
        elif query_type == "semantic":
            results = self.semantic_search(query, limit)
        elif query_type == "hybrid":
            results = self.hybrid_search(query, limit)
        else:
            raise ValueError(f"Invalid query type: {query_type}")

        return self._process_results(results)

    def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        logger.info(f"Performing semantic search: {query}")
        return self.embeddings._embeddings.search(query, limit)

    def sql_search(
        self,
        query: str,
        limit: int = 10,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform SQL search with optional metadata filtering"""
        logger.info(f"Performing SQL search with filters: {metadata_filters}")

        # If query doesn't start with SELECT, wrap it in a basic SELECT
        if not query.strip().upper().startswith("SELECT"):
            query = f"SELECT * FROM txtai WHERE text LIKE '%{query}%'"

        # Add metadata filters
        if metadata_filters:
            where_clause = " AND ".join(
                f"metadata LIKE '%{key}\": \"{value}%'"  # Match JSON string pattern
                for key, value in metadata_filters.items()
            )
            if "WHERE" in query.upper():
                query += f" AND {where_clause}"
            else:
                query += f" WHERE {where_clause}"

        # Add limit
        if not "LIMIT" in query.upper():
            query += f" LIMIT {limit}"

        logger.info(f"Executing SQL query: {query}")
        return self.embeddings._embeddings.search(query)

    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword matching"""
        logger.info(f"Performing hybrid search: {query}")
        # Hybrid search is enabled via config, just use regular search
        return self.embeddings._embeddings.search(query, limit)

    def _process_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardize result format across search types

        Args:
            results: Raw search results from txtai

        Returns:
            List of processed results with consistent format
        """
        processed = []
        for result in results:
            # Parse metadata from JSON string if present
            metadata = {}
            if result.get("metadata"):
                try:
                    metadata = json.loads(result["metadata"])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata: {result['metadata']}")

            # Build standardized result
            processed.append(
                {
                    "id": result.get("id", ""),
                    "text": result.get("text", ""),
                    "score": result.get("score", 0.0),
                    "metadata": metadata,
                }
            )

        return processed
