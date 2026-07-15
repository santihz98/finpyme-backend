from httpx import AsyncClient


async def test_login_exitoso(async_client: AsyncClient, usuario_sabores: dict) -> None:
    r = await async_client.post("/auth/login", json=usuario_sabores)
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["usuario"]["email"] == usuario_sabores["email"]


async def test_login_credenciales_invalidas(async_client: AsyncClient) -> None:
    r = await async_client.post(
        "/auth/login",
        json={"email": "noexiste@test.com", "password": "wrong"},
    )
    assert r.status_code == 401


async def test_get_me_con_token(async_client: AsyncClient, usuario_sabores: dict) -> None:
    login = await async_client.post("/auth/login", json=usuario_sabores)
    token = login.json()["access_token"]

    r = await async_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == usuario_sabores["email"]
    assert "empresa" in body
    assert body["empresa"]["sector"] == "restaurante"


async def test_get_me_sin_token(async_client: AsyncClient) -> None:
    r = await async_client.get("/auth/me")
    assert r.status_code == 403  # HTTPBearer returns 403 when Authorization header is absent
