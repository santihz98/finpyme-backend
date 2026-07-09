from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.periodo import PeriodoCreate, PeriodoResponse, PeriodoSummary
from app.services import periodo_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/periodos", tags=["periodos"])


@router.get("/", response_model=list[PeriodoSummary])
async def list_periodos(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PeriodoSummary]:
    return await periodo_service.get_periodos(current_user.empresa_id, db)  # type: ignore[return-value]


@router.get("/{periodo}", response_model=PeriodoResponse)
async def get_periodo(
    periodo: str,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PeriodoResponse:
    return await periodo_service.get_periodo(current_user.empresa_id, periodo, db)  # type: ignore[return-value]


@router.post("/", response_model=PeriodoResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_periodo(
    body: PeriodoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PeriodoResponse:
    return await periodo_service.upsert_periodo(current_user.empresa_id, body, db)  # type: ignore[return-value]
