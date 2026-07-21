import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.empresa import Empresa
from app.services.auth_service import get_current_empresa

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.post("/generar/{periodo}")
async def generar_reporte(
    periodo: str,
    empresa: Empresa = Depends(get_current_empresa),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    pass  # implementación completa en el siguiente paso
