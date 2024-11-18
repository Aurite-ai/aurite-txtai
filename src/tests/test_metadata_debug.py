import pytest
import json
import logging
from txtai.embeddings import Embeddings
from src.config.settings import Settings
from src.services.embeddings_service import EmbeddingsService
from src.services.query_service import QueryService

logger = logging.getLogger(__name__)


def test_basic_metadata_indexing():
    """Test basic metadata indexing and retrieval directly with txtai"""
    # 1. Use the full config pattern from notebook
    config = {
        "path": "sentence-transformers/nli-mpnet-base-v2",
        "content": True,
        "contentpath": ":memory:",
        "backend": "faiss",
        "hybrid": True,
        "normalize": True,
        "scoring": {
            "method": "bm25",
            "terms": True,
            "normalize": True,
            "weights": {"hybrid": 0.7, "terms": 0.3},
        },
    }
    embeddings = Embeddings(config)

    # 2. Single test document with metadata
    test_doc = {
        "id": "test1",
        "text": "Machine learning test document",
        "metadata": {"category": "tech", "tags": ["test"]},
    }

    # 3. Index with explicit metadata handling
    logger.info("Indexing test document...")
    doc_tuple = (test_doc["id"], test_doc["text"], json.dumps(test_doc["metadata"]))
    embeddings.index([doc_tuple])

    # 4. Try different search approaches
    logger.info("\nTesting searches...")

    # Direct semantic search
    semantic_results = embeddings.search("machine learning", 1)
    logger.info(f"Semantic search result: {semantic_results}")

    # SQL search with exact metadata match
    exact_sql = """
        SELECT *
        FROM txtai
        WHERE metadata LIKE '{"category":"tech"}'
    """
    sql_results = embeddings.search(exact_sql)
    logger.info(f"SQL search result: {sql_results}")

    # SQL search with partial metadata match
    partial_sql = """
        SELECT text, score, metadata
        FROM txtai
        WHERE metadata LIKE '%"category":"tech"%'
    """
    partial_results = embeddings.search(partial_sql)
    logger.info(f"Partial SQL match result: {partial_results}")

    # Raw content check with specific columns
    content_sql = """
        SELECT text, metadata
        FROM txtai
        ORDER BY score DESC
    """
    content_results = embeddings.search(content_sql)
    logger.info(f"Content check result: {content_results}")

    # 5. Assertions with more detail
    assert len(semantic_results) > 0, "Should find document via semantic search"
    if semantic_results:
        result = semantic_results[0]
        logger.info(f"\nDetailed result inspection:")
        logger.info(f"Keys present: {result.keys()}")
        logger.info(f"Full result: {result}")

        # Verify metadata presence and format
        assert "metadata" in result, "Result should include metadata field"
        metadata = result["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        assert isinstance(metadata, dict), "Metadata should be a dict"
        assert metadata["category"] == "tech", "Metadata should contain category"


def test_config_variations():
    """Test different config combinations for metadata handling"""
    configs = [
        {
            "name": "Full Featured",
            "config": {
                "path": "sentence-transformers/nli-mpnet-base-v2",
                "content": True,
                "contentpath": ":memory:",
                "backend": "faiss",
                "hybrid": True,
                "normalize": True,
                "scoring": {
                    "method": "bm25",
                    "terms": True,
                    "normalize": True,
                    "weights": {"hybrid": 0.7, "terms": 0.3},
                },
            },
        }
    ]

    for cfg in configs:
        logger.info(f"\nTesting {cfg['name']} configuration...")
        embeddings = Embeddings(cfg["config"])

        # Test document
        doc = ("test1", "Test document", json.dumps({"category": "test"}))
        embeddings.index([doc])

        results = embeddings.search("test", 1)
        logger.info(f"Search results: {results}")


def test_service_layer_metadata():
    """Test metadata handling through our service layer"""
    logger.info("\nTesting service layer metadata handling...")

    # 1. Setup services with known working config
    settings = Settings(
        EMBEDDINGS_STORAGE_TYPE="memory", EMBEDDINGS_CONTENT_PATH=":memory:"
    )

    embeddings_service = EmbeddingsService(settings)
    embeddings_service.create_index()
    query_service = QueryService(embeddings_service.embeddings, settings)

    # 2. Test document
    test_doc = {
        "id": "test1",
        "text": "Machine learning test document",
        "metadata": {"category": "tech", "tags": ["test"]},
    }

    # 3. Add document and verify indexing
    logger.info("Adding test document...")
    embeddings_service.add_documents([test_doc])

    # 4. Check raw embeddings access
    logger.info("\nChecking raw embeddings...")
    raw_results = embeddings_service.embeddings.search("machine learning", 1)
    logger.info(f"Raw embeddings result: {raw_results}")

    # 5. Test through query service
    logger.info("\nTesting query service...")

    # Semantic search
    semantic_results = query_service.search(
        "machine learning", query_type="semantic", limit=1
    )
    logger.info(f"Semantic search results: {semantic_results}")

    # SQL search
    sql_query = 'SELECT * FROM txtai WHERE metadata LIKE \'%"category":"tech"%\''
    sql_results = query_service.search(sql_query, query_type="sql")
    logger.info(f"SQL search results: {sql_results}")

    # 6. Assertions
    assert len(raw_results) > 0, "Raw embeddings search should find document"
    if raw_results:
        assert "metadata" in raw_results[0], "Raw result should have metadata"

    assert len(semantic_results) > 0, "Semantic search should find document"
    if semantic_results:
        result = semantic_results[0]
        assert "metadata" in result, "Semantic result should have metadata"
        assert isinstance(result["metadata"], dict), "Metadata should be dict"
        assert "category" in result["metadata"], "Metadata should have category"
        assert result["metadata"]["category"] == "tech", "Category should be tech"

    assert len(sql_results) > 0, "SQL search should find document"
    if sql_results:
        assert (
            sql_results[0]["metadata"]["category"] == "tech"
        ), "SQL result should have tech category"


def test_contentpath_variations():
    """Test how different content storage configurations affect metadata"""
    configs = [
        {
            "name": "Memory Content",
            "config": {
                "path": "sentence-transformers/nli-mpnet-base-v2",
                "content": True,
                "contentpath": ":memory:",
                "backend": "faiss",
            },
        },
        {
            "name": "SQLite Content",
            "config": {
                "path": "sentence-transformers/nli-mpnet-base-v2",
                "content": True,
                "contentpath": "txtai/test/debug.db",
                "backend": "faiss",
            },
        },
    ]

    test_doc = ("test1", "Test document", json.dumps({"category": "tech"}))

    for cfg in configs:
        logger.info(f"\nTesting {cfg['name']}...")
        embeddings = Embeddings(cfg["config"])
        embeddings.index([test_doc])

        # Test both search types
        semantic = embeddings.search("test", 1)
        sql = embeddings.search(
            'SELECT * FROM txtai WHERE metadata LIKE \'%"category":"tech"%\''
        )

        logger.info(f"Semantic results: {semantic}")
        logger.info(f"SQL results: {sql}")

        # Verify both searches
        assert len(semantic) > 0, f"{cfg['name']}: Semantic search failed"
        assert len(sql) > 0, f"{cfg['name']}: SQL search failed"


def test_config_vs_service_comparison():
    """Compare direct txtai config vs service layer configuration"""
    logger.info("\n=== Testing Direct txtai Configuration ===")
    # Direct txtai config (known working from first test)
    direct_config = {
        "path": "sentence-transformers/nli-mpnet-base-v2",
        "content": True,
        "contentpath": ":memory:",
        "backend": "faiss",
    }
    direct_embeddings = Embeddings(direct_config)
    logger.info(f"Direct config: {json.dumps(direct_config, indent=2)}")

    # Index test document directly
    test_doc = ("test1", "Test document", json.dumps({"category": "tech"}))
    direct_embeddings.index([test_doc])

    logger.info("\n=== Testing Service Layer Configuration ===")
    # Service layer config
    settings = Settings(
        EMBEDDINGS_STORAGE_TYPE="memory", EMBEDDINGS_CONTENT_PATH=":memory:"
    )
    embeddings_service = EmbeddingsService(settings)
    embeddings_service.create_index()

    # Log the actual config used by service
    service_config = embeddings_service.embeddings.config
    logger.info(f"Service config: {json.dumps(service_config, indent=2)}")

    # Index same document through service
    service_doc = {
        "id": "test1",
        "text": "Test document",
        "metadata": {"category": "tech"},
    }
    embeddings_service.add_documents([service_doc])

    # Compare search results
    logger.info("\n=== Comparing Search Results ===")

    # Direct txtai searches
    direct_semantic = direct_embeddings.search("test", 1)
    direct_sql = direct_embeddings.search(
        'SELECT * FROM txtai WHERE metadata LIKE \'%"category":"tech"%\''
    )
    logger.info(f"Direct semantic results: {direct_semantic}")
    logger.info(f"Direct SQL results: {direct_sql}")

    # Service layer searches
    service_semantic = embeddings_service.embeddings.search("test", 1)
    service_sql = embeddings_service.embeddings.search(
        'SELECT * FROM txtai WHERE metadata LIKE \'%"category":"tech"%\''
    )
    logger.info(f"Service semantic results: {service_semantic}")
    logger.info(f"Service SQL results: {service_sql}")

    # Compare internal state
    logger.info("\n=== Comparing Internal State ===")
    logger.info(f"Direct embeddings count: {direct_embeddings.count()}")
    logger.info(f"Service embeddings count: {embeddings_service.embeddings.count()}")

    # Check if content storage is enabled and working
    logger.info(f"Direct content enabled: {direct_embeddings.config.get('content')}")
    logger.info(f"Service content enabled: {service_config.get('content')}")
