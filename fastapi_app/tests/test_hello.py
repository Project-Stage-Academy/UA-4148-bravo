import httpx
import pytest

@pytest.mark.asyncio
async def test_hello():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/hello")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello from FastAPI"}
