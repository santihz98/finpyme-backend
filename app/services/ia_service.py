import json

import anthropic
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.analisis import Analisis
from app.models.empresa import Empresa
from app.models.periodo import Periodo


def _build_prompt(
    empresa: Empresa,
    periodo: Periodo,
    periodo_anterior: Periodo | None,
) -> str:
    gastos: dict = periodo.data_json.get("gastos", {})
    total_gastos = float(gastos.get("total", periodo.gastos_total))

    gastos_lines = "\n".join(
        f"  · {k.replace('_', ' ').title()}: ${float(v):,.0f} COP"
        f" ({float(v) / total_gastos * 100:.1f}%)"
        for k, v in gastos.items()
        if k != "total" and isinstance(v, (int, float)) and float(v) > 0
    )

    anomalia = periodo.data_json.get("_anomalia")
    anomalia_line = (
        f"\nALERTA: Este mes tuvo una anomalía — {anomalia['descripcion']}"
        if anomalia
        else ""
    )

    if periodo_anterior:
        def pct_var(a: float, b: float) -> str:
            return f"{(a - b) / b * 100:+.1f}%" if b else "N/A"

        anterior_section = (
            f"MES ANTERIOR: {periodo_anterior.periodo}\n"
            f"- Variación ingresos: {pct_var(float(periodo.ingresos_total), float(periodo_anterior.ingresos_total))}\n"
            f"- Variación gastos: {pct_var(float(periodo.gastos_total), float(periodo_anterior.gastos_total))}\n"
            f"- Variación margen: {float(periodo.margen_pct) - float(periodo_anterior.margen_pct):+.1f} pts"
        )
    else:
        anterior_section = "MES ANTERIOR: No disponible"

    return f"""Eres el CFO virtual de {empresa.nombre}, una empresa de {empresa.sector} en {empresa.ciudad}, Colombia.
Analiza los siguientes datos financieros y responde ÚNICAMENTE con JSON válido.

MES ACTUAL: {periodo.periodo}
- Ingresos totales: ${float(periodo.ingresos_total):,.0f} COP
- Gastos totales: ${float(periodo.gastos_total):,.0f} COP
- Utilidad neta: ${float(periodo.utilidad_neta):,.0f} COP
- Margen: {float(periodo.margen_pct):.1f}%
- Composición de gastos:
{gastos_lines}{anomalia_line}

{anterior_section}

INSTRUCCIONES:
- Responde SOLO con JSON, sin markdown, sin explicaciones fuera del JSON
- Usa español colombiano simple, como si hablaras directamente con el dueño
- Sé específico con números cuando refuerces un punto
- Estructura exacta requerida:
{{
  "resumen": "2-3 oraciones directas sobre el estado del negocio este mes",
  "alertas": [
    {{"tipo": "success|warning|danger", "mensaje": "1 oración accionable con número"}}
  ],
  "recomendacion_principal": "1 oración con acción concreta que el dueño puede tomar esta semana"
}}
- Máximo 3 alertas, mínimo 1
- El resumen no puede empezar con "Este mes" """


def _fallback(empresa: Empresa, periodo: Periodo) -> dict:
    margen = float(periodo.margen_pct)
    tipo = "success" if margen >= 20 else "warning" if margen >= 8 else "danger"
    return {
        "resumen": (
            f"En {periodo.periodo}, {empresa.nombre} registró ingresos de "
            f"${float(periodo.ingresos_total):,.0f} COP con gastos de "
            f"${float(periodo.gastos_total):,.0f} COP. "
            f"La utilidad neta fue de ${float(periodo.utilidad_neta):,.0f} COP "
            f"con un margen del {margen:.1f}%."
        ),
        "alertas": [
            {
                "tipo": tipo,
                "mensaje": (
                    f"Margen del {margen:.1f}% — "
                    + (
                        "resultado saludable; mantén el control de costos."
                        if margen >= 20
                        else "por debajo del 20%; revisa la estructura de gastos."
                        if margen >= 8
                        else "nivel crítico; reduce costos o incrementa ingresos urgente."
                    )
                ),
            }
        ],
        "recomendacion_principal": (
            "Compara los gastos del mes con el período anterior e identifica "
            "al menos un rubro donde reducir sin afectar la operación."
        ),
    }


async def generar_analisis(
    empresa: Empresa,
    periodo: Periodo,
    periodo_anterior: Periodo | None,
    db: AsyncSession,
) -> Analisis:
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ANTHROPIC_API_KEY no configurada en el servidor",
        )

    prompt = _build_prompt(empresa, periodo, periodo_anterior)
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text if message.content else ""
    cleaned = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = _fallback(empresa, periodo)

    analisis = Analisis(
        empresa_id=empresa.id,
        periodo_id=periodo.id,
        resumen=parsed["resumen"],
        alertas=parsed.get("alertas", []),
        recomendacion=parsed.get("recomendacion_principal", ""),
        modelo="claude-sonnet-4-6",
        tokens_usados=(
            message.usage.input_tokens + message.usage.output_tokens
            if message.usage
            else None
        ),
    )
    db.add(analisis)
    await db.commit()
    await db.refresh(analisis)
    return analisis
