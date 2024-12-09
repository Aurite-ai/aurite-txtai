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
                config: EmbeddingsConfig = {
                    "path": self.settings.EMBEDDINGS_MODEL,
                    "content": True,
                    "backend": "faiss",
                    "hybrid": True,
                    "functions": {
                        "search": {
                            "function": "hybrid",
                            "weights": {"hybrid": 0.7, "terms": 0.3},
                        },
                    },
                    "batch": self.settings.EMBEDDINGS_BATCH_SIZE,
                    "contentpath": self.settings.EMBEDDINGS_CONTENT_PATH,
                }

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

        except ConnectionError as e:
            logger.error("Database verification failed: %s", str(e))
            raise
        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Unexpected error verifying database: %s", str(e))
            return 0

    async def add(self, documents: list[EmbeddingsDocument]) -> int:
        """Add documents to embeddings index

        Args:
            documents: List of documents to add

        Returns:
            int: Number of documents in the index after addition

        Raises:
            RuntimeError: If service is not initialized
            ValueError: If documents are invalid
            ConnectionError: If indexing fails
        """
        try:
            self._check_initialized()
            if self.embeddings is None:
                raise RuntimeError("Embeddings not initialized")

            logger.info("=== Adding Documents ===")
            logger.info("Processing %d documents", len(documents))

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

        except (ValueError, ConnectionError) as e:
            logger.error("Error adding documents: %s", str(e))
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

            # Execute search
            results = cast(Iterable[Any], self.embeddings.search(query, limit))  # type: ignore[misc] # Complex txtai return type
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

                filtered_results.append(
                    {
                        "text": str(r.get("text", "")),  # type: ignore[union-attr]
                        "score": score,
                        "metadata": json.loads(r.get("metadata", "{}")) if r.get("metadata") else {},  # type: ignore[union-attr]
                        "id": str(r.get("id", "")),  # type: ignore[union-attr]
                    }
                )

            logger.info("Found %d relevant documents above score threshold", len(filtered_results))
            return filtered_results

        except (ValueError, ConnectionError) as e:
            logger.error("Search failed: %s", str(e))
            raise
        except RuntimeError as e:
            logger.error("Unexpected error during search: %s", str(e))
            return []


# Global instance
embeddings_service = EmbeddingsService()
