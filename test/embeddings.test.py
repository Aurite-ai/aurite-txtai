import pytest
from httpx import AsyncClient
from typing import AsyncGenerator

from ..src.main import app  # You'll create this next

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_add_and_search(client: AsyncClient):
    # Test documents
    documents = [
        {"text": "Embeddings are great for semantic search"},
        {"text": "Vector search helps find similar content"},
        {"text": "Natural language processing with transformers"}
    ]
    
    # Add documents
    response = await client.post("/api/embeddings/add", json=documents)
    assert response.status_code == 200
    assert response.json()["count"] == 3
    
    # Search documents
    search_query = {
        "query": "semantic search",
        "limit": 2
    }
    response = await client.post("/api/embeddings/search", json=search_query)
    assert response.status_code == 200
    
    results = response.json()["results"]
    assert len(results) == 2
    assert results[0]["score"] > 0.5  # Assuming normalized similarity scores
