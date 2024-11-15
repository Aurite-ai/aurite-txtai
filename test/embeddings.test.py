import pytest
from httpx import AsyncClient
from typing import AsyncGenerator
import json
import os

from src.main import app

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def test_documents():
    """
    Test document fixture following txtai's example data pattern
    Reference: Notebooks/01_Introducing_txtai.ipynb
    """
    return {
        "documents": [
            {
                "text": "US tops 5 million confirmed virus cases",
                "metadata": {"category": "health", "length": 39}
            },
            {
                "text": "Canada's last fully intact ice shelf has suddenly collapsed",
                "metadata": {"category": "climate", "length": 63}
            },
            {
                "text": "Beijing mobilises invasion craft along coast as Taiwan tensions escalate",
                "metadata": {"category": "politics", "length": 71}
            },
            {
                "text": "Maine man wins $1M from $25 lottery ticket",
                "metadata": {"category": "finance", "length": 44}
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

    # Test SQL query capability
    response = await client.post("/api/embeddings/sql", 
        json={"query": "select count(*), min(length), max(length) from txtai"})
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) > 0

    # Save and load index
    temp_path = "test_index"
    response = await client.post("/api/embeddings/save", json={"path": temp_path})
    assert response.status_code == 200
    
    response = await client.post("/api/embeddings/load", json={"path": temp_path})
    assert response.status_code == 200
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    # Delete documents
    ids = list(range(len(test_documents["documents"])))
    response = await client.post("/api/embeddings/delete", json={"ids": ids})
    assert response.status_code == 200
    assert response.json()["count"] == len(ids)

@pytest.mark.asyncio
async def test_search_variants(client: AsyncClient, test_documents):
    """
    Test different search methods following txtai patterns
    Reference: Notebooks/01_Introducing_txtai.ipynb
    """
    # Add test documents
    await client.post("/api/embeddings/add", json=test_documents)
    
    # Test semantic search
    search_query = {
        "query": "health crisis",
        "limit": 2
    }
    response = await client.post("/api/embeddings/semantic-search", json=search_query)
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    assert all(isinstance(r["score"], float) for r in results)
    
    # Test hybrid search
    search_query = {
        "query": "virus cases",
        "limit": 2,
        "weight": 0.7  # Balance between semantic and keyword matching
    }
    response = await client.post("/api/embeddings/hybrid-search", json=search_query)
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    assert all("scores" in r for r in results)
    
    # Test advanced search with filters
    search_query = {
        "query": "climate change",
        "limit": 2,
        "filters": {"category": "climate"},
        "min_score": 0.1
    }
    response = await client.post("/api/embeddings/advanced-search", json=search_query)
    assert response.status_code == 200
    results = response.json()["results"]
    assert all(r["metadata"]["category"] == "climate" for r in results)
    assert all(r["score"] >= 0.1 for r in results)

@pytest.mark.asyncio
async def test_sql_queries(client: AsyncClient, test_documents):
    """
    Test SQL query capabilities
    Reference: Notebooks/01_Introducing_txtai.ipynb SQL examples
    """
    await client.post("/api/embeddings/add", json=test_documents)
    
    queries = [
        # Basic filtering
        "select text, score from txtai where similar('climate change') and score >= 0.15",
        # Metadata filtering
        "select text, length from txtai where length >= 50",
        # Aggregations
        "select count(*), avg(length) from txtai"
    ]
    
    for query in queries:
        response = await client.post("/api/embeddings/sql", json={"query": query})
        assert response.status_code == 200
        assert "results" in response.json()

@pytest.mark.asyncio
async def test_error_handling(client: AsyncClient):
    """Test error handling for various scenarios"""
    # Test invalid query
    response = await client.post("/api/embeddings/search", json={})
    assert response.status_code == 422
    
    # Test invalid weight
    response = await client.post("/api/embeddings/hybrid-search", 
                               json={"query": "test", "weight": 1.5})
    assert response.status_code == 422
    
    # Test invalid SQL
    response = await client.post("/api/embeddings/sql", 
                               json={"query": "invalid sql"})
    assert response.status_code == 500
