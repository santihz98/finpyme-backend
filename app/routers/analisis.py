from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.analisis import AnalisisIA
from app.models.empresa import Empresa
from app.models.periodo import PeriodoFinanciero
from app.schemas.analisis import AnalisisHistorialItem, AnalisisResponse
from app.services.auth_service import get_current_empresa
from app.services.ia_service import ia_service
from app.services.periodo_service import get_comparativa

router = APIRouter(prefix="/analisis", tags=["analisis"])

_RATE_LIMIT_PER_DAY = 10


async def _check_rate_limit(empresa_id, db: AsyncSession) -> None:
    today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
    count = (
        await db.execute(
            select(func.count(AnalisisIA.id)).where(
                AnalisisIA.empresa_id == empresa_id,
                AnalisisIA.created_at >= today_start,
            )
        )
    ).scalar_one()

    if count >= _RATE_LIMIT_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Límite de {_RATE_LIMIT_PER_DAY} análisis por día alcanzado para esta empresa",
            headers={"Retry-After": "86400"},
        )


def _persist_analisis(
    existing: AnalisisIA | None,
    empresa: Empresa,
    periodo: PeriodoFinanciero,
    generado,
) -> AnalisisIA:
    """Apply generated fields to an existing record or return a new one."""
    alertas = [a.model_dump() for a in generado.alertas]
    if existing:
        existing.resumen = generado.resumen
        existing.alertas_json = alertas
        existing.recomendacion = generado.recomendacion_principal
        existing.modelo_usado = generado.modelo_usado
        existing.tokens_usados = generado.tokens_usados
        return existing

    return AnalisisIA(
        empresa_id=empresa.id,
        periodo_id=periodo.id,
        resumen=generado.resumen,
        alertas_json=alertas,
        recomendacion=generado.recomendacion_principal,
        modelo_usado=generado.modelo_usado,
        tokens_usados=generado.tokens_usados,
    )


# ── POST /analisis/generar/{periodo} ────────────────────────────────────────
# Static prefix "generar" must be declared before /{periodo} to avoid
# FastAPI treating "generar" as a path parameter.

@router.post(
    "/generar/{periodo}",
    response_model=AnalisisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generar(
    periodo: str,
    empresa: Empresa = Depends(get_current_empresa),
    db: AsyncSession = Depends(get_db),
) -> AnalisisResponse:
    await _check_rate_limit(empresa.id, db)

    mes_actual, mes_anterior = await get_comparativa(empresa.id, periodo, db)

    generado = await ia_service.generar_analisis(
        empresa=empresa,
        mes_actual=mes_actual.datos_json,
        mes_anterior=mes_anterior.datos_json if mes_anterior else None,
    )

    # Upsert: overwrite existing analysis for this periodo if present
    existing_result = await db.execute(
        select(AnalisisIA)
        .where(
            AnalisisIA.empresa_id == empresa.id,
            AnalisisIA.periodo_id == mes_actual.id,
        )
        .order_by(desc(AnalisisIA.created_at))
        .limit(1)
    )
    existing = existing_result.scalar_one_or_none()
    record = _persist_analisis(existing, empresa, mes_actual, generado)

    if not existing:
        db.add(record)
    await db.commit()
    await db.refresh(record)
    return AnalisisResponse.model_validate(record)


# ── GET /analisis/historial ─────────────────────────────────────────────────
# Must be declared before /{periodo} so "historial" isn't captured as a param.

@router.get("/historial", response_model=list[AnalisisHistorialItem])
async def historial(
    empresa: Empresa = Depends(get_current_empresa),
    db: AsyncSession = Depends(get_db),
) -> list[AnalisisHistorialItem]:
    result = await db.execute(
        select(AnalisisIA)
        .options(joinedload(AnalisisIA.periodo))
        .where(AnalisisIA.empresa_id == empresa.id)
        .order_by(desc(AnalisisIA.created_at))
    )
    analisis_list = result.scalars().unique().all()

    return [
        AnalisisHistorialItem(
            id=a.id,
            periodo_id=a.periodo_id,
            periodo=a.periodo.periodo,
            resumen=a.resumen,
            recomendacion=a.recomendacion,
            modelo_usado=a.modelo_usado,
            tokens_usados=a.tokens_usados,
            created_at=a.created_at,
        )
        for a in analisis_list
    ]


# ── GET /analisis/{periodo} ─────────────────────────────────────────────────

@router.get("/{periodo}", response_model=AnalisisResponse)
async def get_analisis(
    periodo: str,
    empresa: Empresa = Depends(get_current_empresa),
    db: AsyncSession = Depends(get_db),
) -> AnalisisResponse:
    # Resolve the period string → UUID via a JOIN to avoid a separate query
    result = await db.execute(
        select(AnalisisIA)
        .join(PeriodoFinanciero, AnalisisIA.periodo_id == PeriodoFinanciero.id)
        .where(
            AnalisisIA.empresa_id == empresa.id,
            PeriodoFinanciero.periodo == periodo,
        )
        .order_by(desc(AnalisisIA.created_at))
        .limit(1)
    )
    analisis = result.scalar_one_or_none()

    if analisis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay análisis para el período {periodo}",
        )
    return AnalisisResponse.model_validate(analisis)
