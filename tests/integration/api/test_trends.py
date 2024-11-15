import pytest
from httpx import AsyncClient
from aurite_txtai.main import app

@pytest.mark.asyncio
class TestTrendsAPI:
    async def test_get_trends(self, db_session):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/trends")
            assert response.status_code == 200
            data = response.json()
            assert "trends" in data
    
    async def test_get_domain_trends(self, db_session):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/trends/technology")
            assert response.status_code == 200
            data = response.json()
            assert "trends" in data 