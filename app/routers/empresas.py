from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.schemas.empresa import EmpresaResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.get("/me", response_model=EmpresaResponse)
async def get_mi_empresa(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmpresaResponse:
    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one()
    return empresa  # type: ignore[return-value]
