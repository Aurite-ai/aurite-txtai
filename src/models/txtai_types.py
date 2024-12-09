"""Type definitions for txtai interactions"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict, TypeVar


# Protocol for objects that support dict-like get operations
class DictLike(Protocol):
    """Protocol for objects that support dict-like get operations"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from dict-like object.

        Args:
            key: Key to get value for
            default: Default value if key not found

        Returns:
            Value for key or default if not found
        """
        ...


# Type variable for search results
T = TypeVar("T", bound=dict[str, Any] | DictLike)


class EmbeddingsResult(TypedDict):
    """Type definition for embeddings search result"""

    id: str
    text: str
    score: float
    metadata: dict[str, Any]


class EmbeddingsDocument(TypedDict):
    """Type definition for document to be indexed"""

    id: str
    text: str
    metadata: dict[str, Any]


class LLMResponse(TypedDict):
    """Type definition for LLM response"""

    text: str
    model: str
    usage: dict[str, int]


class RAGResult(TypedDict):
    """Type definition for RAG result"""

    question: str
    context: str
    answer: str
    sources: list[EmbeddingsResult]


class EmbeddingsConfig(TypedDict, total=False):
    """Type definition for embeddings configuration.

    Note: total=False makes all fields optional
    """

    path: str  # Model path
    content: bool  # Enable content storage
    contentpath: str  # Storage path
    backend: str  # Vector storage backend
    hybrid: bool  # Enable hybrid search
    normalize: bool  # Normalize vectors
    functions: dict[str, Any]  # Custom functions
    batch: int  # Batch size
    cloud: dict[str, str]  # Cloud storage config


# Type aliases for txtai return types
TxtaiSearchResult = dict[str, Any] | DictLike | tuple[Any, ...]
TxtaiSearchResults = list[TxtaiSearchResult]
TxtaiIndexDocument = tuple[str, str, str]  # id, text, metadata_json
TxtaiIndexDocuments = list[TxtaiIndexDocument]

# Type alias for txtai search method
TxtaiSearchMethod = Any  # type: ignore # Placeholder for complex txtai search types
