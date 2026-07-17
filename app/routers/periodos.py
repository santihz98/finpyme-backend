from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.empresa import Empresa
from app.models.periodo import PeriodoFinanciero
from app.models.usuario import Usuario
from app.schemas.periodo import (
    ComparativaResponse,
    ImportarMockRequest,
    PeriodoCreate,
    PeriodoListItem,
    PeriodoResumen,
    PeriodoResponse,
    ResumenAnual,
)
from app.services import periodo_service
from app.services.auth_service import get_current_empresa, get_current_user

router = APIRouter(prefix="/periodos", tags=["periodos"])


def _require_owner_or_admin(current_user: Usuario) -> None:
    if current_user.rol not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol owner o admin",
        )


# ── GET /periodos/ ──────────────────────────────────────────────────────────
# Important: static sub-paths (/resumen/anual, /importar-mock) MUST be
# registered before /{periodo} so FastAPI doesn't swallow them as path params.

@router.get("/", response_model=list[PeriodoResumen])
async def list_periodos(
    empresa: Empresa = Depends(get_current_empresa),
    db: AsyncSession = Depends(get_db),
) -> list[PeriodoResumen]:
    return await periodo_service.get_periodos_list(empresa.id, db)


# ── GET /periodos/resumen/anual ─────────────────────────────────────────────

@router.get("/resumen/anual", response_model=ResumenAnual)
async def resumen_anual(
    empresa: Empresa = Depends(get_current_empresa),
    db: AsyncSession = Depends(get_db),
) -> ResumenAnual:
    result = await db.execute(
        select(PeriodoFinanciero).where(PeriodoFinanciero.empresa_id == empresa.id)
    )
    periodos = result.scalars().all()
    return periodo_service.calcular_resumen_anual(list(periodos))


# ── POST /periodos/importar-mock ────────────────────────────────────────────

@router.post(
    "/importar-mock",
    response_model=list[PeriodoResponse],
    status_code=status.HTTP_201_CREATED,
)
async def importar_mock(
    body: ImportarMockRequest,
    empresa: Empresa = Depends(get_current_empresa),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PeriodoResponse]:
    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Endpoint solo disponible en entorno de desarrollo",
        )
    _require_owner_or_admin(current_user)
    periodos = await periodo_service.bulk_upsert_periodos(empresa.id, body, db)
    return periodos  # type: ignore[return-value]


# ── GET /periodos/{periodo} ─────────────────────────────────────────────────

@router.get("/{periodo}", response_model=PeriodoResponse)
async def get_periodo(
    periodo: str,
    empresa: Empresa = Depends(get_current_empresa),
    db: AsyncSession = Depends(get_db),
) -> PeriodoResponse:
    return await periodo_service.get_periodo(empresa.id, periodo, db)  # type: ignore[return-value]


# ── GET /periodos/{periodo}/comparativa ─────────────────────────────────────

@router.get("/{periodo}/comparativa", response_model=ComparativaResponse)
async def get_comparativa(
    periodo: str,
    empresa: Empresa = Depends(get_current_empresa),
    db: AsyncSession = Depends(get_db),
) -> ComparativaResponse:
    actual, anterior = await periodo_service.get_comparativa(empresa.id, periodo, db)
    return ComparativaResponse(
        actual=PeriodoResponse.model_validate(actual),
        anterior=PeriodoResponse.model_validate(anterior) if anterior else None,
    )


# ── POST /periodos/ ─────────────────────────────────────────────────────────

@router.post("/", response_model=PeriodoResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_periodo(
    body: PeriodoCreate,
    empresa: Empresa = Depends(get_current_empresa),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PeriodoResponse:
    _require_owner_or_admin(current_user)
    return await periodo_service.upsert_periodo(empresa.id, body, db)  # type: ignore[return-value]
