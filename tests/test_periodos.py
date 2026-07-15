from httpx import AsyncClient


async def _login(client: AsyncClient, email: str, password: str) -> str:
    r = await client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


async def test_get_periodos_empresa_propia(
    async_client: AsyncClient, usuario_sabores: dict
) -> None:
    token = await _login(async_client, **usuario_sabores)
    r = await async_client.get(
        "/periodos/", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 12
    assert all(p["fuente"] == "mock" for p in data)
    periodos = [p["periodo"] for p in data]
    assert "2025-01" in periodos
    assert "2025-12" in periodos


async def test_aislamiento_multi_tenant(
    async_client: AsyncClient, usuario_sabores: dict, usuario_progreso: dict
) -> None:
    token_s = await _login(async_client, **usuario_sabores)
    r1 = await async_client.get(
        "/periodos/", headers={"Authorization": f"Bearer {token_s}"}
    )
    assert r1.status_code == 200
    ids_sabores = {p["id"] for p in r1.json()}

    token_p = await _login(async_client, **usuario_progreso)
    r2 = await async_client.get(
        "/periodos/", headers={"Authorization": f"Bearer {token_p}"}
    )
    assert r2.status_code == 200
    ids_progreso = {p["id"] for p in r2.json()}

    assert len(ids_sabores) == 12
    assert len(ids_progreso) == 12
    assert ids_sabores.isdisjoint(ids_progreso), "Empresas comparten periodos — falla de aislamiento"


async def test_resumen_anual(async_client: AsyncClient, usuario_sabores: dict) -> None:
    token = await _login(async_client, **usuario_sabores)
    r = await async_client.get(
        "/periodos/resumen/anual", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    data = r.json()

    for field in ("total_ingresos", "total_gastos", "utilidad_total", "margen_promedio",
                  "mejor_mes", "peor_mes", "categorias_ingreso_top", "tendencia_gastos"):
        assert field in data, f"Campo faltante en ResumenAnual: {field}"

    assert isinstance(data["tendencia_gastos"], list)
    assert len(data["tendencia_gastos"]) == 12
    assert data["total_ingresos"] > 0
    assert data["utilidad_total"] > 0
