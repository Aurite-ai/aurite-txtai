import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

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
        }
    ]
}

@pytest.mark.asyncio
async def test_api_workflow():
    """Test complete API workflow including embeddings and LLM endpoints"""
    headers = {"Authorization": f"Bearer {os.getenv('API_KEY')}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test health check
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Test adding food documents
        response = await client.post("/api/embeddings/add", json=test_foods, headers=headers)
        assert response.status_code == 200

        # Test hybrid search
        search_query = {"query": "vegetarian italian", "limit": 2}
        response = await client.post("/api/embeddings/hybrid-search", json=search_query, headers=headers)
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) <= 2
        assert all(isinstance(r["score"], float) for r in results)
        assert any(
            "vegetarian" in r["metadata"]["dietary"] and 
            r["metadata"]["cuisine"] == "Italian" 
            for r in results
        )

        # Test LLM generation
        gen_request = {"prompt": "Write a short greeting"}
        response = await client.post("/api/llm/generate", json=gen_request, headers=headers)
        assert response.status_code == 200
        assert "response" in response.json()
        assert isinstance(response.json()["response"], str)

        # Test LLM context generation
        context_request = {
            "question": "What cuisine types are available?",
            "context": "Available cuisines include Italian and Thai food options."
        }
        response = await client.post("/api/llm/generate-with-context", json=context_request, headers=headers)
        assert response.status_code == 200
        assert "response" in response.json()
        assert isinstance(response.json()["response"], str)
        assert any(cuisine in response.json()["response"].lower() for cuisine in ["italian", "thai"])