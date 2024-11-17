import pytest
from src.services.query_service import QueryService
from src.services.embeddings_service import EmbeddingsService
from src.config.settings import Settings


@pytest.fixture
def query_service(test_settings, test_documents):
    """Provide configured query service with test data"""
    embeddings_service = EmbeddingsService(test_settings)
    embeddings_service.create_index("memory")
    embeddings_service.add_documents(test_documents)
    return QueryService(embeddings_service)


def test_semantic_search(query_service):
    """Test semantic search returns expected results"""
    results = query_service.search("machine learning", query_type="semantic", limit=1)
    assert len(results) == 1
    assert "machine learning" in results[0]["text"].lower()
    assert isinstance(results[0]["score"], float)
    assert "metadata" in results[0]


def test_sql_search(query_service):
    """Test SQL search with metadata filters"""
    results = query_service.search(
        "SELECT * FROM txtai WHERE metadata LIKE '%category\": \"tech%'",
        query_type="sql",
        limit=1,
    )
    assert len(results) == 1
    assert results[0]["metadata"]["category"] == "tech"


def test_hybrid_search(query_service):
    """Test hybrid search combines semantic and keyword matching"""
    results = query_service.search("machine learning", query_type="hybrid", limit=1)
    assert len(results) == 1
    assert isinstance(results[0]["score"], float)
    assert "metadata" in results[0]


def test_invalid_query_type(query_service):
    """Test invalid query type raises error"""
    with pytest.raises(ValueError, match="Invalid query type"):
        query_service.search("test", query_type="invalid")


def test_search_without_index():
    """Test search without creating index first"""
    empty_service = QueryService(EmbeddingsService(Settings()))
    with pytest.raises(ValueError, match="No embeddings index created"):
        empty_service.search("test")


def test_result_format(query_service):
    """Test search results have consistent format"""
    results = query_service.search("test", limit=1)
    assert len(results) == 1
    result = results[0]

    # Check required fields
    assert "id" in result
    assert "text" in result
    assert "score" in result
    assert "metadata" in result

    # Check types
    assert isinstance(result["id"], str)
    assert isinstance(result["text"], str)
    assert isinstance(result["score"], float)
    assert isinstance(result["metadata"], dict)


def test_metadata_parsing(query_service):
    """Test metadata is properly parsed from JSON"""
    results = query_service.search("technical", limit=1)
    assert len(results) == 1
    metadata = results[0]["metadata"]

    # Check metadata structure from test_documents
    assert "category" in metadata
    assert "tags" in metadata
    assert isinstance(metadata["tags"], list)


def test_search_limit(query_service):
    """Test search respects result limit"""
    limit = 2
    results = query_service.search("test", limit=limit)
    assert len(results) <= limit
