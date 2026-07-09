from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AlertaItem(BaseModel):
    tipo: Literal["success", "warning", "danger"]
    mensaje: str


class GenerarAnalisisRequest(BaseModel):
    periodo: str  # "2025-01"


class AnalisisResponse(BaseModel):
    id: int
    empresa_id: int
    periodo_id: int
    resumen: str
    alertas: list[AlertaItem]
    recomendacion: str
    modelo: str
    tokens_usados: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
