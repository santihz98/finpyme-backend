from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PeriodoBase(BaseModel):
    periodo: str  # "2025-01"
    ingresos_total: float
    gastos_total: float
    utilidad_neta: float
    margen_pct: float


class PeriodoCreate(PeriodoBase):
    data_json: dict[str, Any]


class PeriodoSummary(PeriodoBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PeriodoResponse(PeriodoBase):
    id: int
    empresa_id: int
    data_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
