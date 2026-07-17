from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


# ── Request ─────────────────────────────────────────────────────────────────

class PeriodoCreate(BaseModel):
    periodo: str  # "2025-01"
    datos_json: dict[str, Any]
    fuente: str = "manual"


class ImportarMockRequest(BaseModel):
    meses: list[dict[str, Any]]  # lista de objetos MesData del mock-generator
    fuente: str = "mock"


# ── Response: list ───────────────────────────────────────────────────────────

class PeriodoResumen(BaseModel):
    id: UUID
    periodo: str
    fuente: str
    tiene_analisis: bool
    ingresos_total: float
    gastos_total: float
    utilidad_neta: float
    margen_pct: float
    tiene_anomalia: bool
    descripcion_anomalia: str | None
    created_at: datetime


class PeriodoListItem(BaseModel):
    id: UUID
    periodo: str
    fuente: str
    tiene_analisis: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Response: detail ─────────────────────────────────────────────────────────

class PeriodoResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    periodo: str
    fuente: str
    datos_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Response: comparativa ────────────────────────────────────────────────────

class ComparativaResponse(BaseModel):
    actual: PeriodoResponse
    anterior: PeriodoResponse | None


# ── Response: resumen anual ──────────────────────────────────────────────────

class CategoriaIngresoAnual(BaseModel):
    categoria: str
    total: float
    pct: float  # % del total de ingresos anuales


class TendenciaMes(BaseModel):
    periodo: str
    ingresos: float
    gastos: float


class ResumenAnual(BaseModel):
    total_ingresos: float
    total_gastos: float
    utilidad_total: float
    margen_promedio: float
    mejor_mes: str   # periodo con mayor margen
    peor_mes: str    # periodo con menor margen
    categorias_ingreso_top: list[CategoriaIngresoAnual]
    tendencia_gastos: list[TendenciaMes]  # ordenado cronológicamente ASC
