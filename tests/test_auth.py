import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_wrong_credentials(client: AsyncClient) -> None:
    r = await client.post(
        "/auth/login",
        json={"email": "noexiste@test.com", "password": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    r = await client.get("/auth/me")
    assert r.status_code == 403  # HTTPBearer returns 403 when no token
