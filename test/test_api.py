import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app

import pytest
from httpx import AsyncClient, ASGITransport

test_foods = {
    "documents": [
        {
            "text": "Fresh Homemade Italian Pizza Margherita with basil and mozzarella",
            "metadata": {
                "cuisine": "Italian",
                "type": "pizza",
                "price": 15.99,
                "location": "Little Italy, NYC",
                "ingredients": ["tomato sauce", "mozzarella", "basil", "olive oil"],
                "dietary": ["vegetarian"]
            }
        },
        {
            "text": "Spicy Thai Red Curry with coconut milk and jasmine rice",
            "metadata": {
                "cuisine": "Thai", 
                "type": "curry",
                "price": 12.99,
                "location": "Bangkok Kitchen, LA",
                "ingredients": ["coconut milk", "red curry paste", "bamboo shoots", "jasmine rice"],
                "dietary": ["gluten-free"]
            }
        },
        {
            "text": "Classic French Coq au Vin with red wine sauce",
            "metadata": {
                "cuisine": "French",
                "type": "main",
                "price": 24.99,
                "location": "Le Petit Bistro, SF",
                "ingredients": ["chicken", "red wine", "mushrooms", "bacon"],
                "dietary": []
            }
        }
    ]
}

@pytest.mark.asyncio
async def test_api_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test health check
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Test adding food documents
        response = await client.post("/api/embeddings/add", json=test_foods)
        assert response.status_code == 200
        assert response.json()["count"] == 3

        # Test semantic search
        search_query = {"query": "spicy asian food", "limit": 2}
        response = await client.post("/api/embeddings/semantic-search", json=search_query)
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) <= 2
        assert all(isinstance(r["score"], float) for r in results)
        assert any("Thai" in r["metadata"]["cuisine"] for r in results)

        # Test hybrid search
        search_query = {"query": "vegetarian italian", "limit": 2}
        response = await client.post("/api/embeddings/hybrid-search", json=search_query)
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) <= 2
        assert all(isinstance(r["score"], float) for r in results)
        assert any(
            "vegetarian" in r["metadata"]["dietary"] and 
            r["metadata"]["cuisine"] == "Italian" 
            for r in results
        ) 