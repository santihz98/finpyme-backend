import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.empresa import Empresa
from app.models.periodo import PeriodoFinanciero
from app.models.usuario import Usuario
from app.services.auth_service import hash_password

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://finpyme:finpyme_dev@localhost:5432/finpyme_test",
)

DEMO_PASSWORD = "demo1234"

_SEED_EMPRESAS = [
    {
        "nombre": "Sabores de la Abuela S.A.S.",
        "nit": "901.234.567-1",
        "ciudad": "Bogotá",
        "sector": "restaurante",
        "email": "demo@sabores.com",
        "nombre_usuario": "Demo Sabores",
    },
    {
        "nombre": "Distribuidora El Progreso S.A.S.",
        "nit": "900.123.456-7",
        "ciudad": "Medellín",
        "sector": "distribuidora",
        "email": "demo@progreso.com",
        "nombre_usuario": "Demo Progreso",
    },
]


def _make_datos(mes: int) -> dict:
    """Minimal datos_json that satisfies periodo_service._kpis()."""
    ingresos = 10_000_000 + mes * 500_000
    gastos = 7_000_000 + mes * 200_000
    utilidad = ingresos - gastos
    return {
        "periodo": f"2025-{mes:02d}",
        "ingresos": {
            "total": ingresos,
            "categorias": [{"categoria": "ventas", "total": ingresos}],
        },
        "gastos": {"total": gastos},
        "utilidad_neta": utilidad,
        "margen_pct": round(utilidad / ingresos * 100, 1),
    }


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_test_db(engine):
    """Seed test DB with demo companies, users, and 12 periods each."""
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        for data in _SEED_EMPRESAS:
            empresa = Empresa(
                nombre=data["nombre"],
                nit=data["nit"],
                ciudad=data["ciudad"],
                sector=data["sector"],
            )
            session.add(empresa)
            await session.flush()

            session.add(
                Usuario(
                    empresa_id=empresa.id,
                    email=data["email"],
                    password_hash=hash_password(DEMO_PASSWORD),
                    nombre=data["nombre_usuario"],
                    rol="owner",
                )
            )

            for mes in range(1, 13):
                datos = _make_datos(mes)
                session.add(
                    PeriodoFinanciero(
                        empresa_id=empresa.id,
                        periodo=datos["periodo"],
                        datos_json=datos,
                        fuente="mock",
                    )
                )

        await session.commit()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncSession:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(engine) -> AsyncClient:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def usuario_sabores() -> dict:
    return {"email": "demo@sabores.com", "password": DEMO_PASSWORD}


@pytest.fixture(scope="session")
def usuario_progreso() -> dict:
    return {"email": "demo@progreso.com", "password": DEMO_PASSWORD}
