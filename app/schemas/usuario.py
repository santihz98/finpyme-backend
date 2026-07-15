from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.schemas.empresa import EmpresaResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UsuarioResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    email: str
    nombre: str
    rol: str
    activo: bool
    ultimo_login: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MeResponse(UsuarioResponse):
    empresa: EmpresaResponse


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
