import pytest
from httpx import AsyncClient
from typing import AsyncGenerator
import json

from src.main import app

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def test_documents():
    """Test document fixture"""
    return {
        "documents": [
            {
                "text": "Embeddings are great for semantic search",
                "metadata": {"category": "tech", "type": "tutorial"}
            },
            {
                "text": "Vector search helps find similar content",
                "metadata": {"category": "tech", "type": "explanation"}
            },
            {
                "text": "Natural language processing with transformers",
                "metadata": {"category": "tech", "type": "tutorial"}
            },
            {
                "text": "Machine learning models need good training data",
                "metadata": {"category": "tech", "type": "explanation"}
            },
            {
                "text": "Cloud storage enables scalable solutions",
                "metadata": {"category": "cloud", "type": "tutorial"}
            }
        ]
    }

@pytest.mark.asyncio
async def test_document_lifecycle(client: AsyncClient, test_documents):
    """Test complete document lifecycle: add, search, delete"""
    # Add documents
    response = await client.post("/api/embeddings/add", json=test_documents)
    assert response.status_code == 200
    assert response.json()["count"] == len(test_documents["documents"])
    
    # Verify count
    response = await client.get("/api/embeddings/count")
    assert response.status_code == 200
    assert response.json()["count"] == len(test_documents["documents"])
    
    # Delete documents
    ids = list(range(len(test_documents["documents"])))
    response = await client.post("/api/embeddings/delete", json={"ids": ids})
    assert response.status_code == 200
    assert response.json()["count"] == len(ids)

@pytest.mark.asyncio
async def test_simple_search(client: AsyncClient, test_documents):
    """Test semantic search functionality"""
    # Add test documents
    await client.post("/api/embeddings/add", json=test_documents)
    
    # Test semantic search
    search_query = {
        "query": "semantic search technology",
        "limit": 2
    }
    response = await client.post("/api/embeddings/semantic-search", json=search_query)
    assert response.status_code == 200
    
    results = response.json()["results"]
    assert len(results) == 2
    assert all(isinstance(r["score"], float) for r in results)
    assert all("metadata" in r for r in results)

@pytest.mark.asyncio
async def test_hybrid_search(client: AsyncClient, test_documents):
    """Test hybrid search functionality"""
    # Add test documents
    await client.post("/api/embeddings/add", json=test_documents)
    
    # Test hybrid search
    search_query = {
        "query": "vector embeddings",
        "limit": 2,
        "weight": 0.7
    }
    response = await client.post("/api/embeddings/search", json=search_query)
    assert response.status_code == 200
    
    results = response.json()["results"]
    assert len(results) == 2
    assert all("scores" in r for r in results)
    assert all("semantic" in r["scores"] for r in results)
    assert all("keyword" in r["scores"] for r in results)

@pytest.mark.asyncio
async def test_advanced_search(client: AsyncClient, test_documents):
    """Test advanced search with filters and score threshold"""
    # Add test documents
    await client.post("/api/embeddings/add", json=test_documents)
    
    # Test advanced search with filters
    search_query = {
        "query": "tutorial content",
        "limit": 3,
        "filters": {
            "type": "tutorial"
        },
        "min_score": 0.1
    }
    response = await client.post("/api/embeddings/advanced-search", json=search_query)
    assert response.status_code == 200
    
    results = response.json()["results"]
    assert len(results) > 0
    assert all(r["metadata"]["type"] == "tutorial" for r in results)
    assert all(r["score"] >= 0.1 for r in results)

@pytest.mark.asyncio
async def test_batch_processing(client: AsyncClient):
    """Test batch processing with large document set"""
    # Create large document set
    large_documents = {
        "documents": [
            {
                "text": f"Test document {i}",
                "metadata": {"batch": i // 100}
            }
            for i in range(250)  # Create 250 documents
        ]
    }
    
    # Add documents with batch processing
    response = await client.post("/api/embeddings/add", 
                               json=large_documents,
                               params={"batch_size": 100})
    assert response.status_code == 200
    assert response.json()["count"] == 250

@pytest.mark.asyncio
async def test_error_handling(client: AsyncClient):
    """Test error handling for various scenarios"""
    # Test invalid query
    response = await client.post("/api/embeddings/search", json={})
    assert response.status_code == 422
    
    # Test invalid weight
    response = await client.post("/api/embeddings/search", 
                               json={"query": "test", "weight": 1.5})
    assert response.status_code == 422
    
    # Test invalid filters
    response = await client.post("/api/embeddings/advanced-search", 
                               json={"query": "test", "filters": "invalid"})
    assert response.status_code == 422
    
    # Test missing required fields
    response = await client.post("/api/embeddings/add", json={"documents": []})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_metadata_handling(client: AsyncClient, test_documents):
    """Test metadata handling in search results"""
    # Add test documents
    await client.post("/api/embeddings/add", json=test_documents)
    
    # Search with category filter
    search_query = {
        "query": "tutorial",
        "filters": {"category": "tech"},
        "limit": 5
    }
    response = await client.post("/api/embeddings/advanced-search", json=search_query)
    assert response.status_code == 200
    
    results = response.json()["results"]
    assert len(results) > 0
    assert all(r["metadata"]["category"] == "tech" for r in results)
