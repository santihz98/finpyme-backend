from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EmpresaBase(BaseModel):
    nombre: str
    nit: str
    ciudad: str
    sector: str


class EmpresaResponse(EmpresaBase):
    id: UUID
    plan: str
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}
