from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.schemas.usuario import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshRequest,
    TokenResponse,
    UsuarioResponse,
)
from app.schemas.empresa import EmpresaResponse
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    get_current_empresa,
    get_current_user,
    invalidate_refresh_token,
    is_refresh_token_valid,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    result = await db.execute(select(Usuario).where(Usuario.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    user.ultimo_login = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(
        {"sub": str(user.id), "empresa_id": str(user.empresa_id), "rol": user.rol}
    )
    refresh_token = create_refresh_token(user.id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        usuario=UsuarioResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    payload = is_refresh_token_valid(body.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
        )

    from uuid import UUID
    user_id = UUID(payload["sub"])
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    access_token = create_access_token(
        {"sub": str(user.id), "empresa_id": str(user.empresa_id), "rol": user.rol}
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=MeResponse)
async def me(
    current_user: Usuario = Depends(get_current_user),
    empresa: Empresa = Depends(get_current_empresa),
) -> MeResponse:
    return MeResponse(
        **UsuarioResponse.model_validate(current_user).model_dump(),
        empresa=EmpresaResponse.model_validate(empresa),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest) -> None:
    # Blacklists the refresh token's JTI so it can't be used again.
    # The access token remains valid until its natural expiry (24 h).
    invalidate_refresh_token(body.refresh_token)
