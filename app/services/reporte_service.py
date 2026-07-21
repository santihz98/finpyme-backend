import base64
import io
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
from jinja2 import BaseLoader, Environment
from weasyprint import HTML

matplotlib.use("Agg")  # headless backend — no display needed


class ReporteService:

    def __init__(self) -> None:
        self.colores = {
            "emerald": "#00C896",
            "coral": "#FF5C5C",
            "amber": "#F4B942",
            "ink": "#0F1923",
            "slate": "#1A2A3A",
            "pearl": "#E8EDF2",
            "muted": "#6B7A8D",
        }

    async def generar_pdf(
        self,
        empresa: dict,
        mes_data: dict,
        mes_anterior: dict | None,
        analisis: dict | None,
    ) -> bytes:
        datos = mes_data.get("datos_json", mes_data)

        grafica_barras = self._generar_grafica_barras(
            empresa.get("tendencia", [])
        )
        grafica_donut = self._generar_grafica_donut(
            datos.get("gastos", {})
        )

        html_content = self._renderizar_html(
            empresa, mes_data, mes_anterior, analisis,
            grafica_barras, grafica_donut,
        )

        pdf = HTML(string=html_content).write_pdf()
        return pdf

    # ── Gráficas ──────────────────────────────────────────────────────────────

    def _generar_grafica_barras(self, periodos_resumen: list) -> str:
        """Barras agrupadas de ingresos vs gastos (últimos 6 meses). Retorna PNG en base64."""
        fig, ax = plt.subplots(figsize=(8, 3))
        fig.patch.set_facecolor(self.colores["slate"])
        ax.set_facecolor(self.colores["slate"])

        datos = sorted(periodos_resumen[-6:], key=lambda x: x["periodo"])
        meses = [self._nombre_mes_corto(d["periodo"]) for d in datos]
        ingresos = [d["ingresos_total"] / 1_000_000 for d in datos]
        gastos = [d["gastos_total"] / 1_000_000 for d in datos]

        x = range(len(meses))
        width = 0.35

        ax.bar([i - width / 2 for i in x], ingresos, width,
               color=self.colores["emerald"], alpha=0.85, label="Ingresos")
        ax.bar([i + width / 2 for i in x], gastos, width,
               color=self.colores["coral"], alpha=0.85, label="Gastos")

        ax.set_xticks(list(x))
        ax.set_xticklabels(meses, color=self.colores["muted"], fontsize=8)
        ax.tick_params(colors=self.colores["muted"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(self.colores["muted"])
        ax.spines["bottom"].set_color(self.colores["muted"])
        ax.yaxis.set_tick_params(labelcolor=self.colores["muted"])
        ax.set_ylabel("COP Millones", color=self.colores["muted"], fontsize=8)
        ax.legend(facecolor=self.colores["slate"],
                  labelcolor=self.colores["pearl"], fontsize=8)

        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", facecolor=self.colores["slate"],
                    dpi=150, bbox_inches="tight")
        plt.close()
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode()

    def _generar_grafica_donut(self, gastos: dict) -> str:
        """Donut de composición de gastos con porcentajes. Retorna PNG en base64."""
        fig, ax = plt.subplots(figsize=(4, 3))
        fig.patch.set_facecolor(self.colores["slate"])
        ax.set_facecolor(self.colores["slate"])

        categorias = ["Nómina", "Proveedores", "Arriendo", "Servicios", "Otros"]
        valores = [
            gastos.get("nomina", gastos.get("nomina_medica_admin", 0)),
            gastos.get("proveedores", gastos.get("insumos_materiales", 0)),
            gastos.get("arriendo", 0),
            gastos.get("servicios", gastos.get("marketing_digital", 0)),
            gastos.get("otros", 0),
        ]
        colores_donut = ["#378ADD", "#00C896", "#F4B942", "#A78BFA", "#6B7A8D"]

        wedges, texts, autotexts = ax.pie(
            valores,
            colors=colores_donut,
            autopct="%1.0f%%",
            pctdistance=0.75,
            startangle=90,
            wedgeprops={"width": 0.5},
        )
        for text in autotexts:
            text.set_color(self.colores["pearl"])
            text.set_fontsize(7)

        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", facecolor=self.colores["slate"],
                    dpi=150, bbox_inches="tight")
        plt.close()
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode()

    # ── Helpers de fecha ─────────────────────────────────────────────────────

    def _nombre_mes_corto(self, periodo: str) -> str:
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                 "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        return meses[int(periodo.split("-")[1]) - 1]

    def _nombre_mes_completo(self, periodo: str) -> str:
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        año = periodo.split("-")[0]
        return f"{meses[int(periodo.split('-')[1]) - 1]} {año}"

    # ── Renderizado HTML ──────────────────────────────────────────────────────

    def _renderizar_html(
        self,
        empresa: dict,
        mes_data: dict,
        mes_anterior: dict | None,
        analisis: dict | None,
        grafica_barras: str,
        grafica_donut: str,
    ) -> str:
        datos = mes_data.get("datos_json", mes_data)
        ingresos = datos.get("ingresos", {})
        gastos = datos.get("gastos", {})
        utilidad = datos.get("utilidad_neta", 0)
        margen = datos.get("margen_pct", 0)

        var_ingresos = var_margen = None
        if mes_anterior:
            datos_ant = mes_anterior.get("datos_json", mes_anterior)
            ing_ant = datos_ant.get("ingresos", {})
            ing_ant_total = ing_ant.get("total", 0) if isinstance(ing_ant, dict) else ing_ant
            ing_actual = ingresos.get("total", 0) if isinstance(ingresos, dict) else ingresos
            if ing_ant_total:
                var_ingresos = round((ing_actual - ing_ant_total) / ing_ant_total * 100, 1)
            mar_ant = datos_ant.get("margen_pct", 0)
            var_margen = round(margen - mar_ant, 1)

        env = Environment(loader=BaseLoader())
        tpl = env.from_string(_HTML_TEMPLATE)
        return tpl.render(
            empresa=empresa,
            periodo=mes_data.get("periodo", ""),
            ingresos_total=ingresos.get("total", 0) if isinstance(ingresos, dict) else ingresos,
            gastos_total=gastos.get("total", 0) if isinstance(gastos, dict) else gastos,
            utilidad=utilidad,
            margen=margen,
            var_ingresos=var_ingresos,
            var_margen=var_margen,
            categorias=ingresos.get("categorias", []) if isinstance(ingresos, dict) else [],
            analisis=analisis,
            anomalia=datos.get("_anomalia"),
            grafica_barras=grafica_barras,
            grafica_donut=grafica_donut,
            fmt=self._formatear_cop,
            generado_en=datetime.now().strftime("%d/%m/%Y %H:%M"),
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _formatear_cop(self, valor: float) -> str:
        if valor >= 1_000_000:
            return f"${valor / 1_000_000:.1f}M"
        return f"${valor / 1_000:.0f}K"


# ── Template HTML ─────────────────────────────────────────────────────────────

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<style>
  @page { size: A4; margin: 20mm 15mm; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Helvetica Neue', Arial, sans-serif;
         background: #0F1923; color: #E8EDF2; font-size: 11px; }
  .header { background: #1A2A3A; padding: 16px 20px;
            border-bottom: 3px solid #00C896; margin-bottom: 16px; }
  .header h1 { font-size: 18px; color: #00C896; }
  .header .sub { color: #6B7A8D; font-size: 11px; margin-top: 4px; }
  .kpis { display: flex; gap: 10px; margin-bottom: 16px; }
  .kpi { flex: 1; background: #1A2A3A; border-radius: 8px;
         padding: 12px; border-left: 3px solid #00C896; }
  .kpi.rojo { border-left-color: #FF5C5C; }
  .kpi .label { color: #6B7A8D; font-size: 9px; text-transform: uppercase;
                letter-spacing: .5px; }
  .kpi .valor { font-size: 20px; font-weight: 700; color: #E8EDF2;
                margin: 4px 0 2px; }
  .kpi .var { font-size: 9px; }
  .var-pos { color: #00C896; } .var-neg { color: #FF5C5C; }
  .seccion { background: #1A2A3A; border-radius: 8px;
             padding: 12px 14px; margin-bottom: 12px; }
  .seccion h2 { font-size: 12px; color: #00C896; margin-bottom: 10px;
                border-bottom: 1px solid #0F1923; padding-bottom: 6px; }
  .graficas { display: flex; gap: 10px; margin-bottom: 12px; }
  .graficas .g-barras { flex: 2; }
  .graficas .g-donut  { flex: 1; }
  .graficas img { width: 100%; border-radius: 6px; }
  table { width: 100%; border-collapse: collapse; font-size: 10px; }
  th { color: #6B7A8D; text-align: left; padding: 4px 6px;
       border-bottom: 1px solid #0F1923; }
  td { padding: 5px 6px; border-bottom: 1px solid #0F1923; }
  .tag-anomalia { background: #F4B942; color: #0F1923; border-radius: 4px;
                  padding: 2px 6px; font-size: 9px; font-weight: 700; }
  .analisis-bloque { background: #0F1923; border-radius: 6px;
                     padding: 10px 12px; font-size: 10px;
                     line-height: 1.5; color: #E8EDF2; }
  .footer { text-align: center; color: #6B7A8D; font-size: 8px;
            margin-top: 10px; }
</style>
</head>
<body>

<div class="header">
  <h1>{{ empresa.nombre }}</h1>
  <div class="sub">Reporte financiero · {{ periodo }} · NIT {{ empresa.nit }}</div>
</div>

<div class="kpis">
  <div class="kpi">
    <div class="label">Ingresos</div>
    <div class="valor">{{ fmt(ingresos_total) }}</div>
    {% if var_ingresos is not none %}
    <div class="var {% if var_ingresos >= 0 %}var-pos{% else %}var-neg{% endif %}">
      {{ '+' if var_ingresos >= 0 }}{{ var_ingresos }}% vs mes anterior
    </div>
    {% endif %}
  </div>
  <div class="kpi {% if utilidad < 0 %}rojo{% endif %}">
    <div class="label">Gastos</div>
    <div class="valor">{{ fmt(gastos_total) }}</div>
  </div>
  <div class="kpi {% if utilidad < 0 %}rojo{% endif %}">
    <div class="label">Utilidad neta</div>
    <div class="valor">{{ fmt(utilidad) }}</div>
    {% if var_margen is not none %}
    <div class="var {% if var_margen >= 0 %}var-pos{% else %}var-neg{% endif %}">
      Margen {{ margen }}% ({{ '+' if var_margen >= 0 }}{{ var_margen }}pp)
    </div>
    {% endif %}
  </div>
</div>

{% if anomalia %}
<div class="seccion">
  <span class="tag-anomalia">⚠ Anomalía detectada</span>
  <span style="margin-left:8px;color:#F4B942;">{{ anomalia.descripcion }}</span>
</div>
{% endif %}

<div class="graficas">
  <div class="g-barras">
    <div class="seccion">
      <h2>Tendencia mensual</h2>
      <img src="data:image/png;base64,{{ grafica_barras }}" alt="Tendencia"/>
    </div>
  </div>
  <div class="g-donut">
    <div class="seccion">
      <h2>Composición de gastos</h2>
      <img src="data:image/png;base64,{{ grafica_donut }}" alt="Gastos"/>
    </div>
  </div>
</div>

{% if categorias %}
<div class="seccion">
  <h2>Desglose de ingresos</h2>
  <table>
    <tr><th>Categoría</th><th style="text-align:right">Valor</th><th style="text-align:right">%</th></tr>
    {% for cat in categorias %}
    <tr>
      <td>{{ cat.nombre }}</td>
      <td style="text-align:right">{{ fmt(cat.valor) }}</td>
      <td style="text-align:right">
        {{ "%.1f"|format(cat.valor / ingresos_total * 100) if ingresos_total else 0 }}%
      </td>
    </tr>
    {% endfor %}
  </table>
</div>
{% endif %}

{% if analisis %}
<div class="seccion">
  <h2>Análisis IA</h2>
  <div class="analisis-bloque">{{ analisis.resumen }}</div>
  {% if analisis.recomendacion %}
  <div class="analisis-bloque" style="margin-top:8px;border-left:3px solid #00C896;padding-left:10px;">
    <strong style="color:#00C896;">Recomendación:</strong> {{ analisis.recomendacion }}
  </div>
  {% endif %}
</div>
{% endif %}

<div class="footer">Generado el {{ generado_en }} · FinPyme · Confidencial</div>
</body>
</html>
"""
