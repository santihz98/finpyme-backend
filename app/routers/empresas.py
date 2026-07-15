from fastapi import APIRouter, Depends

from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaResponse
from app.services.auth_service import get_current_empresa

router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.get("/me", response_model=EmpresaResponse)
async def get_mi_empresa(
    empresa: Empresa = Depends(get_current_empresa),
) -> EmpresaResponse:
    return EmpresaResponse.model_validate(empresa)
