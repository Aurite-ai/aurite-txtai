import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app

# Load environment variables from .env file
load_dotenv()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_health_check(client):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


@pytest.mark.asyncio
async def test_get_trends(client):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/trends", headers={"X-API-Key": os.getenv("API_KEY")})
    assert response.status_code == 200
    assert "summary" in response.json()
    assert "trends" in response.json()


@pytest.mark.asyncio
async def test_get_sports_trends(client):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/trends/sports", headers={"X-API-Key": os.getenv("API_KEY")})
    assert response.status_code == 200
    assert "summary" in response.json()
    assert "trends" in response.json()


@pytest.mark.asyncio
async def test_get_cooking_trends(client):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/trends/cooking", headers={"X-API-Key": os.getenv("API_KEY")})
    assert response.status_code == 200
    assert "summary" in response.json()
    assert "trends" in response.json()


@pytest.mark.asyncio
async def test_get_gaming_trends(client):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/trends/gaming", headers={"X-API-Key": os.getenv("API_KEY")})
    assert response.status_code == 200
    assert "summary" in response.json()
    assert "trends" in response.json()


@pytest.mark.asyncio
async def test_get_finance_trends(client):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/trends/finance", headers={"X-API-Key": os.getenv("API_KEY")})
    assert response.status_code == 200
    assert "summary" in response.json()
    assert "trends" in response.json()


@pytest.mark.asyncio
async def test_get_technology_trends(client):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/trends/technology", headers={"X-API-Key": os.getenv("API_KEY")})
    assert response.status_code == 200
    assert "summary" in response.json()
    assert "trends" in response.json()


@pytest.mark.asyncio
async def test_get_ideas(client):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/ideas", headers={"X-API-Key": os.getenv("API_KEY")})
    assert response.status_code == 200
    assert "summary" in response.json()
    assert "ideas" in response.json()


@pytest.mark.asyncio
async def test_get_statistics(client):
    trend_name = "Some Trend Name"  # Replace with an actual trend name from your database
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            f"/statistics/{trend_name}", headers={"X-API-Key": os.getenv("API_KEY")}
        )
    assert response.status_code == 200
    assert "trend" in response.json()
    assert "statistics" in response.json()
