"""
Seed script — creates demo companies, users, and financial periods.

Local:   python scripts/seed.py
Docker:  docker compose --profile seed run --rm seed
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.empresa import Empresa
from app.models.periodo import PeriodoFinanciero
from app.models.usuario import Usuario
from app.services.auth_service import hash_password

MOCK_DATA_PATH = Path(
    os.getenv(
        "MOCK_DATA_PATH",
        str(Path(__file__).parent.parent.parent / "finpyme-mock-generator" / "output"),
    )
)

SEED_DATA = [
    {
        "empresa": {
            "nombre": "Sabores de la Abuela S.A.S.",
            "nit": "901.234.567-1",
            "ciudad": "Bogotá",
            "sector": "restaurante",
        },
        "usuario": {
            "email": "demo@sabores.com",
            "password": "demo1234",
            "nombre": "Demo Sabores",
            "rol": "owner",
        },
        "mock_file": "sabores_abuela_2025.json",
    },
    {
        "empresa": {
            "nombre": "Distribuidora El Progreso S.A.S.",
            "nit": "900.123.456-7",
            "ciudad": "Medellín",
            "sector": "distribuidora",
        },
        "usuario": {
            "email": "demo@progreso.com",
            "password": "demo1234",
            "nombre": "Demo Progreso",
            "rol": "owner",
        },
        "mock_file": "distribuidora_progreso_2025.json",
    },
    {
        "empresa": {
            "nombre": "Clínica Estética Vitalia S.A.S.",
            "nit": "900.987.654-3",
            "ciudad": "Cali",
            "sector": "clinica",
        },
        "usuario": {
            "email": "demo@vitalia.com",
            "password": "demo1234",
            "nombre": "Demo Vitalia",
            "rol": "owner",
        },
        "mock_file": "clinica_vitalia_2025.json",
    },
]


async def _delete_empresa(session: AsyncSession, nit: str) -> None:
    try:
        result = await session.execute(select(Empresa).where(Empresa.nit == nit))
    except Exception:
        await session.rollback()
        return  # tables don't exist yet — first run after migration
    empresa = result.scalar_one_or_none()
    if empresa is None:
        return
    await session.execute(
        delete(PeriodoFinanciero).where(PeriodoFinanciero.empresa_id == empresa.id)
    )
    await session.execute(delete(Usuario).where(Usuario.empresa_id == empresa.id))
    await session.execute(delete(Empresa).where(Empresa.id == empresa.id))


async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    results = []

    async with factory() as session:
        print("Limpiando datos previos...")
        for entry in SEED_DATA:
            await _delete_empresa(session, entry["empresa"]["nit"])
        await session.commit()

        print("Insertando datos de demo...")
        for entry in SEED_DATA:
            empresa = Empresa(**entry["empresa"])
            session.add(empresa)
            await session.flush()

            u = entry["usuario"]
            session.add(
                Usuario(
                    empresa_id=empresa.id,
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    nombre=u["nombre"],
                    rol=u["rol"],
                )
            )

            mock_path = MOCK_DATA_PATH / entry["mock_file"]
            periodos_count = 0
            if mock_path.exists():
                data = json.loads(mock_path.read_text(encoding="utf-8"))
                for mes in data.get("meses", []):
                    session.add(
                        PeriodoFinanciero(
                            empresa_id=empresa.id,
                            periodo=mes["periodo"],
                            datos_json=mes,
                            fuente="mock",
                        )
                    )
                    periodos_count += 1
            else:
                print(f"  ⚠  Mock file no encontrado: {mock_path}")

            results.append(
                {
                    "nombre": entry["empresa"]["nombre"],
                    "email": u["email"],
                    "password": u["password"],
                    "periodos": periodos_count,
                }
            )

        await session.commit()

    await engine.dispose()

    col = (32, 26, 12, 9)
    sep = "─" * (sum(col) + len(col) * 3 + 1)
    print(f"\n{sep}")
    print(
        f"  {'Empresa':<{col[0]}} {'Email':<{col[1]}} {'Password':<{col[2]}} {'Periodos':>{col[3]}}"
    )
    print(sep)
    for r in results:
        nombre = r["nombre"][:col[0]] if len(r["nombre"]) <= col[0] else r["nombre"][: col[0] - 2] + ".."
        print(
            f"  {nombre:<{col[0]}} {r['email']:<{col[1]}} {r['password']:<{col[2]}} {r['periodos']:>{col[3]}}"
        )
    print(sep)
    print(f"  Seed completado: {len(results)} empresas insertadas.\n")


if __name__ == "__main__":
    asyncio.run(seed())
