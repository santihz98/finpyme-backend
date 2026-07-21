import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analisis import AnalisisIA
from app.models.empresa import Empresa
from app.models.periodo import PeriodoFinanciero
from app.models.usuario import Usuario
from app.services.auth_service import get_current_empresa
from app.services.email_service import EmailService
from app.services.reporte_service import ReporteService

router = APIRouter(prefix="/reportes", tags=["reportes"])
reporte_service = ReporteService()
email_service = EmailService()


async def _construir_datos_reporte(
    periodo: str, current_empresa: Empresa, db: AsyncSession
) -> dict:
    # 1. Periodo solicitado
    result = await db.execute(
        select(PeriodoFinanciero).where(
            PeriodoFinanciero.empresa_id == current_empresa.id,
            PeriodoFinanciero.periodo == periodo,
        )
    )
    mes_actual = result.scalar_one_or_none()
    if not mes_actual:
        raise HTTPException(404, f"Periodo {periodo} no encontrado")

    # 2. Mes anterior
    año, mes = periodo.split("-")
    mes_int = int(mes)
    periodo_anterior = f"{int(año)-1}-12" if mes_int == 1 else f"{año}-{mes_int-1:02d}"

    result_ant = await db.execute(
        select(PeriodoFinanciero).where(
            PeriodoFinanciero.empresa_id == current_empresa.id,
            PeriodoFinanciero.periodo == periodo_anterior,
        )
    )
    mes_anterior = result_ant.scalar_one_or_none()

    # 3. Todos los periodos para la gráfica de barras
    result_all = await db.execute(
        select(PeriodoFinanciero)
        .where(PeriodoFinanciero.empresa_id == current_empresa.id)
        .order_by(PeriodoFinanciero.periodo)
    )
    todos_periodos = result_all.scalars().all()

    periodos_resumen = [
        {
            "periodo": p.periodo,
            "ingresos_total": p.datos_json.get("ingresos", {}).get("total", 0),
            "gastos_total": p.datos_json.get("gastos", {}).get("total", 0),
        }
        for p in todos_periodos
    ]

    # 4. Análisis IA más reciente del periodo (opcional)
    result_analisis = await db.execute(
        select(AnalisisIA)
        .where(
            AnalisisIA.empresa_id == current_empresa.id,
            AnalisisIA.periodo_id == mes_actual.id,
        )
        .order_by(AnalisisIA.created_at.desc())
        .limit(1)
    )
    analisis_obj = result_analisis.scalar_one_or_none()
    analisis = None
    if analisis_obj:
        analisis = {
            "resumen": analisis_obj.resumen,
            "alertas": analisis_obj.alertas_json,
            "recomendacion_principal": analisis_obj.recomendacion,
        }

    # 5. Datos de empresa
    empresa_dict = {
        "nombre": current_empresa.nombre,
        "nit": current_empresa.nit,
        "ciudad": current_empresa.ciudad,
        "sector": current_empresa.sector,
    }

    # 6. Gráficas
    grafica_barras = reporte_service._generar_grafica_barras(periodos_resumen)
    grafica_donut = reporte_service._generar_grafica_donut(
        mes_actual.datos_json.get("gastos", {})
    )

    return {
        "empresa": empresa_dict,
        "mes_data": {
            "periodo": mes_actual.periodo,
            "datos_json": mes_actual.datos_json,
            "utilidad_neta": mes_actual.datos_json.get("utilidad_neta", 0),
            "margen_pct": mes_actual.datos_json.get("margen_pct", 0),
        },
        "mes_anterior": {"datos_json": mes_anterior.datos_json} if mes_anterior else None,
        "analisis": analisis,
        "periodos_resumen": periodos_resumen,
        "grafica_barras": grafica_barras,
        "grafica_donut": grafica_donut,
    }


@router.post("/generar/{periodo}")
async def generar_reporte(
    periodo: str,
    current_empresa: Empresa = Depends(get_current_empresa),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    datos = await _construir_datos_reporte(periodo, current_empresa, db)

    pdf_bytes = await reporte_service.generar_pdf(
        empresa=datos["empresa"],
        mes_data=datos["mes_data"],
        mes_anterior=datos["mes_anterior"],
        analisis=datos["analisis"],
        periodos_resumen=datos["periodos_resumen"],
        grafica_barras=datos["grafica_barras"],
        grafica_donut=datos["grafica_donut"],
    )

    nombre_archivo = (
        f"reporte-finpyme-"
        f"{current_empresa.nombre.lower().replace(' ', '-')}-"
        f"{periodo}.pdf"
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
    )


@router.post("/enviar-email/{periodo}")
async def enviar_reporte_email(
    periodo: str,
    current_empresa: Empresa = Depends(get_current_empresa),
    db: AsyncSession = Depends(get_db),
):
    datos = await _construir_datos_reporte(periodo, current_empresa, db)

    result_user = await db.execute(
        select(Usuario).where(
            Usuario.empresa_id == current_empresa.id,
            Usuario.rol == "owner",
        ).limit(1)
    )
    usuario = result_user.scalar_one_or_none()
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")

    enviado = await email_service.enviar_reporte_mensual(
        email_destino=usuario.email,
        nombre_usuario=usuario.nombre,
        empresa=datos["empresa"],
        mes_data=datos["mes_data"],
        mes_anterior=datos["mes_anterior"],
        analisis=datos["analisis"],
        periodos_resumen=datos["periodos_resumen"],
        grafica_barras=datos["grafica_barras"],
        grafica_donut=datos["grafica_donut"],
    )

    return {
        "enviado": enviado,
        "email": usuario.email,
        "periodo": periodo,
    }
