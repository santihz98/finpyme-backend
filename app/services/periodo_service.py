from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import desc, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analisis import AnalisisIA
from app.models.periodo import PeriodoFinanciero
from app.schemas.periodo import (
    CategoriaIngresoAnual,
    ImportarMockRequest,
    PeriodoCreate,
    PeriodoListItem,
    PeriodoResumen,
    ResumenAnual,
    TendenciaMes,
)


# ── KPI extraction helper ────────────────────────────────────────────────────

def _kpis(datos: dict) -> tuple[float, float, float, float]:
    """Returns (ingresos, gastos, utilidad, margen) from datos_json."""
    ing = datos.get("ingresos", {})
    ingresos = float(ing.get("total", 0) if isinstance(ing, dict) else ing)
    g = datos.get("gastos", {})
    gastos = float(g.get("total", 0) if isinstance(g, dict) else g)
    utilidad = float(datos.get("utilidad_neta", 0))
    margen = float(datos.get("margen_pct", 0))
    return ingresos, gastos, utilidad, margen


# ── List ─────────────────────────────────────────────────────────────────────

async def get_periodos_list(
    empresa_id: UUID, db: AsyncSession
) -> list[PeriodoResumen]:
    analisis_exists = (
        exists(select(AnalisisIA.id).where(AnalisisIA.periodo_id == PeriodoFinanciero.id))
        .correlate(PeriodoFinanciero)
    )
    stmt = (
        select(PeriodoFinanciero, analisis_exists.label("tiene_analisis"))
        .where(PeriodoFinanciero.empresa_id == empresa_id)
        .order_by(desc(PeriodoFinanciero.periodo))
    )
    rows = (await db.execute(stmt)).all()
    result = []
    for row in rows:
        p = row[0]
        ing, gas, util, margen = _kpis(p.datos_json)
        anomalia = p.datos_json.get("_anomalia")
        result.append(
            PeriodoResumen(
                id=p.id,
                periodo=p.periodo,
                fuente=p.fuente,
                tiene_analisis=bool(row[1]),
                ingresos_total=round(ing, 2),
                gastos_total=round(gas, 2),
                utilidad_neta=round(util, 2),
                margen_pct=round(margen, 2),
                tiene_anomalia=anomalia is not None,
                descripcion_anomalia=anomalia.get("descripcion") if anomalia else None,
                created_at=p.created_at,
            )
        )
    return result


# ── Single fetch ─────────────────────────────────────────────────────────────

async def get_periodo(
    empresa_id: UUID, periodo_str: str, db: AsyncSession
) -> PeriodoFinanciero:
    result = await db.execute(
        select(PeriodoFinanciero).where(
            PeriodoFinanciero.empresa_id == empresa_id,
            PeriodoFinanciero.periodo == periodo_str,
        )
    )
    periodo = result.scalar_one_or_none()
    if periodo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Periodo {periodo_str} no encontrado",
        )
    return periodo


# ── Comparativa ──────────────────────────────────────────────────────────────

async def get_comparativa(
    empresa_id: UUID, periodo_str: str, db: AsyncSession
) -> tuple[PeriodoFinanciero, PeriodoFinanciero | None]:
    actual = await get_periodo(empresa_id, periodo_str, db)

    prev = await db.execute(
        select(PeriodoFinanciero)
        .where(
            PeriodoFinanciero.empresa_id == empresa_id,
            PeriodoFinanciero.periodo < periodo_str,
        )
        .order_by(desc(PeriodoFinanciero.periodo))
        .limit(1)
    )
    anterior = prev.scalar_one_or_none()
    return actual, anterior


# ── Upsert (single) ──────────────────────────────────────────────────────────

async def upsert_periodo(
    empresa_id: UUID, data: PeriodoCreate, db: AsyncSession
) -> PeriodoFinanciero:
    result = await db.execute(
        select(PeriodoFinanciero).where(
            PeriodoFinanciero.empresa_id == empresa_id,
            PeriodoFinanciero.periodo == data.periodo,
        )
    )
    periodo = result.scalar_one_or_none()

    if periodo:
        periodo.datos_json = data.datos_json
        periodo.fuente = data.fuente
    else:
        periodo = PeriodoFinanciero(
            empresa_id=empresa_id,
            periodo=data.periodo,
            datos_json=data.datos_json,
            fuente=data.fuente,
        )
        db.add(periodo)

    await db.commit()
    await db.refresh(periodo)
    return periodo


# ── Bulk import (mock) ───────────────────────────────────────────────────────

async def bulk_upsert_periodos(
    empresa_id: UUID, body: ImportarMockRequest, db: AsyncSession
) -> list[PeriodoFinanciero]:
    # Fetch all existing periods for this empresa in one query
    existing_result = await db.execute(
        select(PeriodoFinanciero).where(PeriodoFinanciero.empresa_id == empresa_id)
    )
    existing: dict[str, PeriodoFinanciero] = {
        p.periodo: p for p in existing_result.scalars().all()
    }

    upserted: list[PeriodoFinanciero] = []
    for mes in body.meses:
        periodo_str: str = mes.get("periodo", "")
        if not periodo_str:
            continue

        if periodo_str in existing:
            existing[periodo_str].datos_json = mes
            existing[periodo_str].fuente = body.fuente
            upserted.append(existing[periodo_str])
        else:
            nuevo = PeriodoFinanciero(
                empresa_id=empresa_id,
                periodo=periodo_str,
                datos_json=mes,
                fuente=body.fuente,
            )
            db.add(nuevo)
            upserted.append(nuevo)

    await db.commit()
    for p in upserted:
        await db.refresh(p)
    return upserted


# ── Resumen anual (pure computation) ─────────────────────────────────────────

def calcular_resumen_anual(periodos: list[PeriodoFinanciero]) -> ResumenAnual:
    if not periodos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay períodos registrados para esta empresa",
        )

    total_ing = 0.0
    total_gas = 0.0
    total_util = 0.0
    margenes: list[float] = []
    mejor = peor = periodos[0]
    cat_totales: dict[str, float] = defaultdict(float)
    tendencia: list[TendenciaMes] = []

    for p in sorted(periodos, key=lambda x: x.periodo):  # ASC for trend
        ing, gas, util, margen = _kpis(p.datos_json)
        total_ing += ing
        total_gas += gas
        total_util += util
        margenes.append(margen)

        if margen > _kpis(mejor.datos_json)[3]:
            mejor = p
        if margen < _kpis(peor.datos_json)[3]:
            peor = p

        # Aggregate categorías de ingreso
        ingresos_data = p.datos_json.get("ingresos", {})
        if isinstance(ingresos_data, dict):
            for cat in ingresos_data.get("categorias", []):
                nombre = cat.get("nombre", "otro")
                cat_totales[nombre] += float(cat.get("valor", 0))

        tendencia.append(TendenciaMes(periodo=p.periodo, ingresos=ing, gastos=gas))

    margen_promedio = sum(margenes) / len(margenes)

    cats_sorted = sorted(cat_totales.items(), key=lambda x: x[1], reverse=True)
    categorias_top = [
        CategoriaIngresoAnual(
            categoria=nombre,
            total=round(total, 2),
            pct=round(total / total_ing * 100, 1) if total_ing else 0.0,
        )
        for nombre, total in cats_sorted[:3]
    ]

    return ResumenAnual(
        total_ingresos=round(total_ing, 2),
        total_gastos=round(total_gas, 2),
        utilidad_total=round(total_util, 2),
        margen_promedio=round(margen_promedio, 2),
        mejor_mes=mejor.periodo,
        peor_mes=peor.periodo,
        categorias_ingreso_top=categorias_top,
        tendencia_gastos=tendencia,
    )
