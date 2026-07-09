from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analisis import Analisis
from app.models.empresa import Empresa
from app.models.periodo import Periodo
from app.models.usuario import Usuario
from app.schemas.analisis import AnalisisResponse, GenerarAnalisisRequest
from app.services import ia_service, periodo_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/analisis", tags=["analisis"])


@router.post(
    "/generar", response_model=AnalisisResponse, status_code=status.HTTP_201_CREATED
)
async def generar(
    body: GenerarAnalisisRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalisisResponse:
    periodo = await periodo_service.get_periodo(
        current_user.empresa_id, body.periodo, db
    )

    # Fetch the immediately preceding period for comparison
    prev_result = await db.execute(
        select(Periodo)
        .where(
            Periodo.empresa_id == current_user.empresa_id,
            Periodo.periodo < body.periodo,
        )
        .order_by(desc(Periodo.periodo))
        .limit(1)
    )
    periodo_anterior = prev_result.scalar_one_or_none()

    empresa_result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = empresa_result.scalar_one()

    return await ia_service.generar_analisis(empresa, periodo, periodo_anterior, db)  # type: ignore[return-value]


@router.get("/{periodo}", response_model=AnalisisResponse)
async def get_analisis(
    periodo: str,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalisisResponse:
    p = await periodo_service.get_periodo(current_user.empresa_id, periodo, db)

    result = await db.execute(
        select(Analisis)
        .where(
            Analisis.empresa_id == current_user.empresa_id,
            Analisis.periodo_id == p.id,
        )
        .order_by(desc(Analisis.created_at))
        .limit(1)
    )
    analisis = result.scalar_one_or_none()
    if analisis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay análisis para {periodo}",
        )
    return analisis  # type: ignore[return-value]
