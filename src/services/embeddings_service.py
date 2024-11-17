from pathlib import Path
import json
import logging
from typing import List, Dict, Any, Optional

from txtai.embeddings import Embeddings

from ..config.settings import Settings
from ..config.embeddings_config import get_embeddings_config

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service to manage txtai embeddings operations

    Based on patterns from embeddings notebooks (01-04)
    """

    def __init__(self, settings: Settings):
        """Initialize embeddings service

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._embeddings: Optional[Embeddings] = None

    def create_index(
        self, storage_type: str = "memory", index_path: str = "txtai/content.db"
    ) -> None:
        """Create a new embeddings index with specified storage configuration

        Args:
            storage_type: Type of storage ("memory", "sqlite", "cloud")
            index_path: Path for persistent storage (only used for sqlite)

        Raises:
            ValueError: If invalid storage type specified
        """
        # Validate storage type first
        if storage_type not in ["memory", "sqlite", "cloud"]:
            raise ValueError(f"Invalid storage type: {storage_type}")

        # Update settings for this index
        self.settings.EMBEDDINGS_STORAGE_TYPE = storage_type
        self.settings.EMBEDDINGS_CONTENT_PATH = index_path

        # Get configuration
        config = get_embeddings_config(self.settings)

        logger.info(f"Creating new embeddings index with {storage_type} storage")
        self._embeddings = Embeddings(config)

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the embeddings index

        Args:
            documents: List of documents with format:
                {
                    "id": str,
                    "text": str,
                    "metadata": dict
                }

        Raises:
            ValueError: If no embeddings index created
        """
        if not self._embeddings:
            raise ValueError("No embeddings index created. Call create_index() first")

        # Convert documents to txtai format (id, text, metadata)
        indexed_docs = [
            (str(doc["id"]), doc["text"], json.dumps(doc.get("metadata", {})))
            for doc in documents
        ]

        logger.info(f"Adding {len(documents)} documents to index")
        self._embeddings.index(indexed_docs)

    def save_index(self, path: str) -> None:
        """Save the current index to specified path

        Args:
            path: Path to save index

        Raises:
            ValueError: If no embeddings index created
        """
        if not self._embeddings:
            raise ValueError("No embeddings index created")

        logger.info(f"Saving embeddings index to {path}")
        self._embeddings.save(path)

    def load_index(self, path: str) -> None:
        """Load an existing index from specified path

        Args:
            path: Path to load index from

        Raises:
            ValueError: If no embeddings index created
        """
        if not self._embeddings:
            raise ValueError("No embeddings index created")

        logger.info(f"Loading embeddings index from {path}")
        self._embeddings.load(path)
