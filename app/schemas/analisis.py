from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class AlertaItem(BaseModel):
    tipo: Literal["success", "warning", "danger"]
    mensaje: str


# ── Service output (not yet persisted) ───────────────────────────────────────

class AnalisisGenerado(BaseModel):
    """Returned by IAService.generar_analisis — Claude's parsed response."""
    resumen: str
    alertas: list[AlertaItem]
    recomendacion_principal: str
    modelo_usado: str
    tokens_usados: int


# ── DB-backed API responses ───────────────────────────────────────────────────

class AnalisisResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    periodo_id: UUID
    resumen: str
    alertas_json: list[AlertaItem]
    recomendacion: str
    modelo_usado: str
    tokens_usados: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalisisHistorialItem(BaseModel):
    id: UUID
    periodo_id: UUID
    periodo: str          # "2025-01" — populated via JOIN in the router
    resumen: str
    recomendacion: str
    modelo_usado: str
    tokens_usados: int
    created_at: datetime
