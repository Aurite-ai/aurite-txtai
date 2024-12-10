"""Embeddings service for managing document indexing and semantic search.

This module provides a service for managing document embeddings using txtai.
It handles document indexing, hybrid search, and database verification.
"""

from __future__ import annotations

from collections.abc import Iterable
import json
import logging
from typing import TYPE_CHECKING, Any, cast

from src.models.txtai_types import DictLike, EmbeddingsConfig, EmbeddingsDocument, EmbeddingsResult, TxtaiIndexDocuments
from src.services.base_service import BaseService
from txtai.embeddings import Embeddings


if TYPE_CHECKING:
    from src.config import Settings


logger = logging.getLogger(__name__)


def validate_document(doc: Any) -> None:
    """Validate document fields.

    Args:
        doc: Document to validate

    Raises:
        KeyError: If required field is missing
        TypeError: If field has invalid type
    """
    # Check required fields
    for field in ["id", "text", "metadata"]:
        if field not in doc:
            raise KeyError(f"Missing required field: {field}")

    # Check field types
    if not isinstance(doc["id"], str):
        raise TypeError("Field 'id' must be string")
    if not isinstance(doc["text"], str):
        raise TypeError("Field 'text' must be string")
    if not isinstance(doc["metadata"], dict):
        raise TypeError("Field 'metadata' must be dict")

    # Check for None values
    if doc["id"] is None:
        raise TypeError("Field 'id' cannot be None")
    if doc["text"] is None:
        raise TypeError("Field 'text' cannot be None")
    if doc["metadata"] is None:
        raise TypeError("Field 'metadata' cannot be None")


def create_embeddings_config(settings: Settings) -> EmbeddingsConfig:
    """Create embeddings configuration from settings.

    Args:
        settings: Application settings

    Returns:
        EmbeddingsConfig: Configuration dictionary for txtai embeddings
    """
    config: EmbeddingsConfig = {
        "path": settings.EMBEDDINGS_MODEL,
        "content": True,
        "backend": "faiss",
        "hybrid": True,
        "normalize": True,
        "database": True,
        "storetokens": True,
        "storeannoy": True,
        "scoring": {
            "method": "bm25",
            "terms": True,
            "normalize": True,
            "weights": {"hybrid": 0.7, "terms": 0.3},
        },
        "batch": settings.EMBEDDINGS_BATCH_SIZE,
        "contentpath": settings.EMBEDDINGS_CONTENT_PATH,
    }

    # Add cloud storage configuration if needed
    if settings.EMBEDDINGS_STORAGE_TYPE == "cloud":
        config["cloud"] = {
            "provider": "gcs",
            "container": settings.GOOGLE_CLOUD_BUCKET,
            "prefix": settings.EMBEDDINGS_PREFIX,
        }
        config["contentpath"] = f"gcs://{settings.GOOGLE_CLOUD_BUCKET}"

    return config


class EmbeddingsService(BaseService):
    """Service for managing document embeddings and search"""

    def __init__(self) -> None:
        """Initialize embeddings service"""
        super().__init__()
        self.embeddings: Embeddings | None = None

    async def initialize(self, settings: Settings, **kwargs: Any) -> None:
        """Initialize embeddings with configuration

        Args:
            settings: Application settings containing embeddings configuration
            **kwargs: Additional configuration options

        Raises:
            RuntimeError: If service is already initialized
            ValueError: If configuration is invalid
            ConnectionError: If embeddings backend fails to connect
        """
        try:
            await super().initialize(settings, **kwargs)

            if not self._initialized:
                logger.info("=== Initializing Embeddings ===")
                config = create_embeddings_config(settings)

                # Initialize embeddings
                self.embeddings = Embeddings(config)

                self._initialized = True
                logger.info("Embeddings initialized successfully")

        except (ValueError, ConnectionError) as e:
            logger.error("Failed to initialize embeddings: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error initializing embeddings: %s", str(e))
            raise RuntimeError(f"Failed to initialize embeddings: {e!s}") from e

    async def verify_database(self) -> int:
        """Verify database is initialized and return count of embeddings

        Returns:
            int: Number of embeddings in database

        Raises:
            RuntimeError: If service is not initialized
            ConnectionError: If database verification fails
        """
        try:
            self._check_initialized()
            if self.embeddings is None:
                raise RuntimeError("Embeddings not initialized")

            logger.info("Verifying with query: SELECT COUNT(*) as count FROM txtai")
            result = self.embeddings.search("SELECT COUNT(*) as count FROM txtai")
            if not result or not isinstance(result, list):
                return 0

            # Handle various return types from txtai search
            first_result = result[0]
            if isinstance(first_result, dict | DictLike):  # type: ignore[misc] # Pylance doesn't understand DictLike
                count = cast(int, first_result.get("count", 0))  # type: ignore[union-attr] # Complex txtai return type
            elif isinstance(first_result, tuple):
                count = cast(int, first_result[0])
            else:
                count = 0

            logger.info("Verified count: %d", count)
            return count

        except (RuntimeError, ConnectionError) as e:
            logger.error("Database verification failed: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error verifying database: %s", str(e))
            raise RuntimeError(f"Failed to verify database: {e!s}") from e

    async def add(self, documents: list[EmbeddingsDocument]) -> int:
        """Add documents to embeddings index

        Args:
            documents: List of documents to add

        Returns:
            int: Number of documents in the index after addition

        Raises:
            RuntimeError: If service is not initialized
            ValueError: If documents are invalid
            KeyError: If document is missing required fields
            TypeError: If document fields have invalid types
            ConnectionError: If indexing fails
        """
        try:
            self._check_initialized()
            if self.embeddings is None:
                raise RuntimeError("Embeddings not initialized")

            logger.info("=== Adding Documents ===")
            logger.info("Processing %d documents", len(documents))

            # Validate all documents first
            for doc in documents:
                validate_document(doc)

            # Format documents for txtai
            formatted_docs: TxtaiIndexDocuments = [
                (
                    str(doc["id"]),
                    str(doc["text"]),
                    json.dumps(doc["metadata"]),
                )
                for doc in documents
            ]

            # Index documents
            self.embeddings.index(formatted_docs)
            logger.info("Documents indexed successfully")

            # Verify count
            return await self.verify_database()

        except (RuntimeError, ValueError, ConnectionError) as e:
            logger.error("Error adding documents: %s", str(e))
            raise
        except (KeyError, TypeError) as e:
            # Let KeyError and TypeError propagate directly
            logger.error("Document validation error: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error adding documents: %s", str(e))
            raise RuntimeError(f"Failed to add documents: {e!s}") from e

    async def hybrid_search(self, query: str, limit: int = 5, min_score: float = 0.0) -> list[EmbeddingsResult]:
        """Perform hybrid search on embeddings

        Args:
            query: Search query
            limit: Maximum number of results
            min_score: Minimum score threshold

        Returns:
            list[EmbeddingsResult]: List of search results

        Raises:
            RuntimeError: If service is not initialized
            ValueError: If query is invalid
            ConnectionError: If search fails
        """
        try:
            self._check_initialized()
            if self.embeddings is None:
                raise RuntimeError("Embeddings not initialized")

            # Handle empty query
            if not query.strip():
                return []

            # Check if it's a SQL query
            is_sql = query.strip().upper().startswith("SELECT")
            if is_sql:
                # For SQL queries, ensure we're using tags for metadata
                if "metadata" in query:
                    query = query.replace("metadata", "tags")

                # Add ORDER BY and LIMIT clauses if not present and not a COUNT query
                if "COUNT" not in query.upper():
                    # Get all matching documents first
                    base_query = query
                    if "ORDER BY" not in base_query.upper():
                        base_query = f"{base_query} ORDER BY id"
                    if "LIMIT" not in base_query.upper():
                        base_query = f"{base_query} LIMIT 1000"  # Get all matching documents

                    # Execute SQL query
                    results = self.embeddings.search(base_query)
                else:
                    results = self.embeddings.search(query)

                if not results:
                    return []

                # Format SQL results
                formatted_results: list[EmbeddingsResult] = []
                for r in results:
                    if not isinstance(r, dict | DictLike) or not hasattr(r, "get"):  # type: ignore[misc]
                        continue

                    # Parse metadata from tags
                    tags = r.get("tags", "{}")  # type: ignore[union-attr]
                    try:
                        metadata = json.loads(str(tags))
                    except json.JSONDecodeError:
                        metadata = {}

                    formatted_results.append(
                        {
                            "id": str(r.get("id", "")),  # type: ignore[union-attr]
                            "text": str(r.get("text", "")),  # type: ignore[union-attr]
                            "score": 1.0,  # SQL results don't have scores
                            "metadata": metadata,
                        }
                    )

                # Apply limit after formatting
                return formatted_results[:limit]

            # Execute semantic search
            results = cast(Iterable[Any], self.embeddings.search(query, limit))  # type: ignore[misc]
            if not results:
                return []

            # Filter and format results
            filtered_results: list[EmbeddingsResult] = []
            for r in results:
                if not isinstance(r, dict | DictLike) or not hasattr(r, "get"):  # type: ignore[misc]
                    continue

                score = float(r.get("score", 0.0))  # type: ignore[union-attr]
                if score <= min_score:
                    continue

                # Parse metadata from tags
                tags = r.get("tags", "{}")  # type: ignore[union-attr]
                try:
                    metadata = json.loads(str(tags))
                except json.JSONDecodeError:
                    metadata = {}

                filtered_results.append(
                    {
                        "id": str(r.get("id", "")),  # type: ignore[union-attr]
                        "text": str(r.get("text", "")),  # type: ignore[union-attr]
                        "score": score,
                        "metadata": metadata,
                    }
                )

            return filtered_results

        except (RuntimeError, ValueError, ConnectionError) as e:
            logger.error("Error performing search: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error during search: %s", str(e))
            raise RuntimeError(f"Failed to perform search: {e!s}") from e


# Global instance
embeddings_service = EmbeddingsService()
