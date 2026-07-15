import json

import anthropic
from pydantic import ValidationError

from app.config import settings
from app.models.empresa import Empresa
from app.schemas.analisis import AlertaItem, AnalisisGenerado


def _kpis(datos: dict) -> tuple[float, float, float, float]:
    """Returns (ingresos, gastos, utilidad, margen) from a datos_json dict."""
    ing = datos.get("ingresos", {})
    ingresos = float(ing.get("total", 0) if isinstance(ing, dict) else ing)
    g = datos.get("gastos", {})
    gastos = float(g.get("total", 0) if isinstance(g, dict) else g)
    return ingresos, gastos, float(datos.get("utilidad_neta", 0)), float(datos.get("margen_pct", 0))


class _ClaudeOutput(AnalisisGenerado):
    """Internal Pydantic model for validating Claude's raw JSON response."""
    modelo_usado: str = ""
    tokens_usados: int = 0


class IAService:
    def __init__(self) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-6"

    async def generar_analisis(
        self,
        empresa: Empresa,
        mes_actual: dict,
        mes_anterior: dict | None,
    ) -> AnalisisGenerado:
        if not settings.ANTHROPIC_API_KEY:
            return self._fallback(empresa, mes_actual)

        prompt = self._construir_prompt(empresa, mes_actual, mes_anterior)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=600,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text if response.content else ""
        tokens = (
            response.usage.input_tokens + response.usage.output_tokens
            if response.usage
            else 0
        )
        parsed = self._parsear_respuesta(raw, empresa, mes_actual)

        return AnalisisGenerado(
            resumen=parsed["resumen"],
            alertas=parsed["alertas"],
            recomendacion_principal=parsed["recomendacion_principal"],
            modelo_usado=self.model,
            tokens_usados=tokens,
        )

    def _construir_prompt(
        self,
        empresa: Empresa,
        mes_actual: dict,
        mes_anterior: dict | None,
    ) -> str:
        periodo_str: str = mes_actual.get("periodo", "")
        ingresos, gastos_total, utilidad, margen = _kpis(mes_actual)

        gastos_dict: dict = mes_actual.get("gastos", {})
        gastos_lines = "\n".join(
            f"  · {k.replace('_', ' ').title()}: ${float(v):,.0f} COP"
            f" ({float(v) / gastos_total * 100:.1f}%)"
            for k, v in gastos_dict.items()
            if k != "total" and isinstance(v, (int, float)) and float(v) > 0
        ) if gastos_total else "  · Sin detalle de gastos"

        anomalia = mes_actual.get("_anomalia")
        anomalia_line = (
            f"\nALERTA: Anomalía detectada — {anomalia['descripcion']}"
            if anomalia
            else ""
        )

        if mes_anterior:
            pi, pg, _, pm = _kpis(mes_anterior)

            def pct_var(a: float, b: float) -> str:
                return f"{(a - b) / b * 100:+.1f}%" if b else "N/A"

            anterior_section = (
                f"MES ANTERIOR: {mes_anterior.get('periodo', '')}\n"
                f"- Variación ingresos: {pct_var(ingresos, pi)}\n"
                f"- Variación gastos: {pct_var(gastos_total, pg)}\n"
                f"- Variación margen: {margen - pm:+.1f} pts"
            )
        else:
            anterior_section = "MES ANTERIOR: No disponible"

        return (
            f"Eres el CFO virtual de {empresa.nombre}, una empresa de "
            f"{empresa.sector} en {empresa.ciudad}, Colombia.\n"
            "Analiza los siguientes datos financieros y responde ÚNICAMENTE con JSON válido.\n\n"
            f"MES ACTUAL: {periodo_str}\n"
            f"- Ingresos totales: ${ingresos:,.0f} COP\n"
            f"- Gastos totales: ${gastos_total:,.0f} COP\n"
            f"- Utilidad neta: ${utilidad:,.0f} COP\n"
            f"- Margen: {margen:.1f}%\n"
            f"- Composición de gastos:\n{gastos_lines}{anomalia_line}\n\n"
            f"{anterior_section}\n\n"
            "INSTRUCCIONES:\n"
            "- Responde SOLO con JSON, sin markdown, sin explicaciones fuera del JSON\n"
            "- Usa español colombiano simple, como si hablaras directamente con el dueño\n"
            "- Sé específico con números cuando refuerces un punto\n"
            "- Estructura exacta requerida:\n"
            "{\n"
            '  "resumen": "2-3 oraciones directas sobre el estado del negocio este mes",\n'
            '  "alertas": [\n'
            '    {"tipo": "success|warning|danger", "mensaje": "1 oración accionable con número"}\n'
            "  ],\n"
            '  "recomendacion_principal": "1 oración con acción concreta que el dueño puede tomar esta semana"\n'
            "}\n"
            "- Máximo 3 alertas, mínimo 1\n"
            "- El resumen no puede empezar con \"Este mes\""
        )

    def _parsear_respuesta(
        self, raw: str, empresa: Empresa, mes_actual: dict
    ) -> dict:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(cleaned)
            validated = _ClaudeOutput(**data)
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError, KeyError):
            return self._fallback(empresa, mes_actual)

    def _fallback(self, empresa: Empresa, mes_actual: dict) -> dict:
        ingresos, gastos, utilidad, margen = _kpis(mes_actual)
        tipo: str = "success" if margen >= 20 else "warning" if margen >= 8 else "danger"
        return {
            "resumen": (
                f"En {mes_actual.get('periodo', 'el período')}, {empresa.nombre} registró "
                f"ingresos de ${ingresos:,.0f} COP con gastos de ${gastos:,.0f} COP. "
                f"La utilidad neta fue de ${utilidad:,.0f} COP con un margen del {margen:.1f}%."
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


# Module-level singleton — AsyncAnthropic client is coroutine-safe
ia_service = IAService()
