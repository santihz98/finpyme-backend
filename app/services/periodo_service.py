from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.periodo import Periodo
from app.schemas.periodo import PeriodoCreate


async def get_periodos(empresa_id: int, db: AsyncSession) -> list[Periodo]:
    result = await db.execute(
        select(Periodo)
        .where(Periodo.empresa_id == empresa_id)
        .order_by(desc(Periodo.periodo))
    )
    return list(result.scalars().all())


async def get_periodo(empresa_id: int, periodo_str: str, db: AsyncSession) -> Periodo:
    result = await db.execute(
        select(Periodo).where(
            Periodo.empresa_id == empresa_id,
            Periodo.periodo == periodo_str,
        )
    )
    periodo = result.scalar_one_or_none()
    if periodo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Periodo {periodo_str} no encontrado",
        )
    return periodo


async def upsert_periodo(
    empresa_id: int, data: PeriodoCreate, db: AsyncSession
) -> Periodo:
    result = await db.execute(
        select(Periodo).where(
            Periodo.empresa_id == empresa_id,
            Periodo.periodo == data.periodo,
        )
    )
    periodo = result.scalar_one_or_none()

    if periodo:
        for field, value in data.model_dump().items():
            setattr(periodo, field, value)
    else:
        periodo = Periodo(empresa_id=empresa_id, **data.model_dump())
        db.add(periodo)

    await db.commit()
    await db.refresh(periodo)
    return periodo
