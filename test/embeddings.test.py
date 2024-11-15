import pytest
from httpx import AsyncClient
from typing import AsyncGenerator

from src.main import app

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_add_and_search(client: AsyncClient):
    # Test documents
    request = {
        "documents": [
            {
                "text": "Embeddings are great for semantic search",
                "metadata": {"category": "tech", "type": "example"}
            },
            {
                "text": "Vector search helps find similar content",
                "metadata": {"category": "tech", "type": "example"}
            },
            {
                "text": "Natural language processing with transformers",
                "metadata": {"category": "tech", "type": "example"}
            }
        ]
    }
    
    # Add documents
    response = await client.post("/api/embeddings/add", json=request)
    assert response.status_code == 200
    assert response.json()["count"] == 3
    
    # Search documents
    search_query = {
        "query": "semantic search",
        "limit": 2,
        "hybrid_weight": 0.7
    }
    response = await client.post("/api/embeddings/search", json=search_query)
    assert response.status_code == 200
    
    results = response.json()["results"]
    assert len(results) == 2
    assert results[0]["score"] > 0.5  # Assuming normalized similarity scores
    assert "semantic" in results[0]["scores"]  # Check hybrid search scores
    assert "keyword" in results[0]["scores"]
