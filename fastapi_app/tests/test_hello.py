import httpx
import pytest

@pytest.mark.asyncio
async def test_hello():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/fastapi/hello")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello from FastAPI"}

@pytest.mark.asyncio
async def test_healthcheck():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/fastapi/healthcheck")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}