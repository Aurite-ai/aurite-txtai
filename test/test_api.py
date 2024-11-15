import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app

import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_api_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test health check
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Test adding documents
        documents = {
            "documents": [
                {
                    "text": "Classic Italian Pasta Carbonara",
                    "metadata": {"cuisine": "Italian", "type": "pasta"}
                },
                {
                    "text": "Homemade Minestrone Soup",
                    "metadata": {"cuisine": "Italian", "type": "soup"}
                }
            ]
        }
        response = await client.post("/api/embeddings/add", json=documents)
        assert response.status_code == 200
        assert response.json()["count"] == 2

        # Test semantic search
        search_query = {"query": "Italian cuisine", "limit": 2}
        response = await client.post("/api/embeddings/semantic-search", json=search_query)
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) <= 2
        assert all(isinstance(r["score"], float) for r in results)

        # Test hybrid search
        search_query = {"query": "soup recipes", "limit": 2}
        response = await client.post("/api/embeddings/search", json=search_query)
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) <= 2
        assert all("scores" in r for r in results) 