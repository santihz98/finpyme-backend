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
        periodos_resumen: list,
    ) -> bytes:
        datos = mes_data.get("datos_json", mes_data)

        grafica_barras = self._generar_grafica_barras(periodos_resumen)
        grafica_donut = self._generar_grafica_donut(datos.get("gastos", {}))

        html_content = self._renderizar_html(
            empresa, mes_data, mes_anterior, analisis,
            periodos_resumen, grafica_barras, grafica_donut,
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
        periodos_resumen: list,
        grafica_barras: str,
        grafica_donut: str,
    ) -> str:
        datos_json = mes_data.get("datos_json", {})
        ingresos = datos_json.get("ingresos", {})
        gastos = datos_json.get("gastos", {})

        delta_ingresos = None
        if mes_anterior:
            anterior_json = mes_anterior.get("datos_json", {})
            ant_ingresos = anterior_json.get("ingresos", {}).get("total", 0)
            if ant_ingresos > 0:
                delta_ingresos = (
                    (ingresos.get("total", 0) - ant_ingresos) / ant_ingresos * 100
                )

        total_ingresos = ingresos.get("total", 0)
        categorias = [
            {
                "nombre": cat["nombre"],
                "valor_fmt": self._formatear_cop(cat["valor"]),
                "pct": round(cat["valor"] / total_ingresos * 100, 1) if total_ingresos else 0,
            }
            for cat in ingresos.get("categorias", [])
        ]

        env = Environment(loader=BaseLoader())
        template = env.from_string(REPORTE_HTML_TEMPLATE)
        return template.render(
            empresa=empresa,
            periodo_label=self._nombre_mes_completo(mes_data["periodo"]),
            ingresos_fmt=self._formatear_cop(total_ingresos),
            gastos_fmt=self._formatear_cop(gastos.get("total", 0)),
            utilidad_fmt=self._formatear_cop(datos_json.get("utilidad_neta", 0)),
            margen=round(datos_json.get("margen_pct", 0), 1),
            delta_ingresos=delta_ingresos,
            grafica_barras=grafica_barras,
            grafica_donut=grafica_donut,
            categorias=categorias,
            analisis=analisis,
            fecha_generacion=datetime.now().strftime("%d/%m/%Y %H:%M"),
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _formatear_cop(self, valor: float) -> str:
        if valor >= 1_000_000:
            return f"${valor / 1_000_000:.1f}M"
        return f"${valor / 1_000:.0f}K"


# ── Template HTML ─────────────────────────────────────────────────────────────

REPORTE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, Arial, sans-serif;
    background: #0F1923;
    color: #E8EDF2;
    padding: 32px;
    font-size: 13px;
  }
  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 28px;
    padding-bottom: 20px;
    border-bottom: 1px solid #243447;
  }
  .logo { font-size: 22px; font-weight: 700; }
  .logo span { color: #00C896; }
  .empresa-info { text-align: right; }
  .empresa-nombre { font-size: 15px; font-weight: 600; }
  .empresa-meta { font-size: 11px; color: #6B7A8D; margin-top: 3px; }
  .periodo-badge {
    display: inline-block;
    background: #1A2A3A;
    border: 1px solid #243447;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    color: #00C896;
    margin-top: 6px;
  }
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 24px;
  }
  .kpi-card {
    background: #1A2A3A;
    border: 1px solid #243447;
    border-radius: 10px;
    padding: 14px;
    border-left: 3px solid #243447;
  }
  .kpi-card.emerald { border-left-color: #00C896; }
  .kpi-card.coral   { border-left-color: #FF5C5C; }
  .kpi-card.amber   { border-left-color: #F4B942; }
  .kpi-label { font-size: 10px; color: #6B7A8D; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
  .kpi-valor { font-size: 20px; font-weight: 700; }
  .kpi-delta { font-size: 10px; margin-top: 4px; }
  .emerald { color: #00C896; }
  .coral   { color: #FF5C5C; }
  .amber   { color: #F4B942; }
  .section-title {
    font-size: 12px;
    font-weight: 600;
    color: #6B7A8D;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 12px;
  }
  .charts-row {
    display: grid;
    grid-template-columns: 3fr 2fr;
    gap: 16px;
    margin-bottom: 24px;
  }
  .chart-card {
    background: #1A2A3A;
    border: 1px solid #243447;
    border-radius: 10px;
    padding: 14px;
  }
  .chart-card img { width: 100%; height: auto; }
  .table-card {
    background: #1A2A3A;
    border: 1px solid #243447;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 24px;
  }
  table { width: 100%; border-collapse: collapse; }
  th {
    font-size: 10px; color: #6B7A8D; text-transform: uppercase;
    text-align: left; padding: 6px 8px;
    border-bottom: 1px solid #243447;
  }
  td {
    font-size: 12px; padding: 8px 8px;
    border-bottom: 1px solid #1A2A3A;
  }
  .ai-card {
    background: #1A2A3A;
    border: 1px solid #243447;
    border-left: 3px solid #00C896;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 24px;
  }
  .ai-resumen { font-size: 12px; line-height: 1.6; color: #E8EDF2; margin-bottom: 12px; }
  .alerta {
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 11px;
    margin-bottom: 6px;
  }
  .alerta.success { background: rgba(0,200,150,0.1);  color: #00C896; }
  .alerta.warning { background: rgba(244,185,66,0.1); color: #F4B942; }
  .alerta.danger  { background: rgba(255,92,92,0.1);  color: #FF5C5C; }
  .recomendacion {
    background: rgba(244,185,66,0.08);
    border: 1px solid rgba(244,185,66,0.2);
    border-radius: 6px;
    padding: 10px 12px;
    font-size: 11px;
    color: #F4B942;
    margin-top: 10px;
  }
  .footer {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #243447;
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #6B7A8D;
  }
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="logo">Fin<span>Pyme</span></div>
    <div style="font-size:10px; color:#6B7A8D; margin-top:3px;">Reporte financiero ejecutivo</div>
  </div>
  <div class="empresa-info">
    <div class="empresa-nombre">{{ empresa.nombre }}</div>
    <div class="empresa-meta">NIT {{ empresa.nit }} · {{ empresa.ciudad }}</div>
    <div class="periodo-badge">{{ periodo_label }}</div>
  </div>
</div>

<div class="kpi-grid">
  <div class="kpi-card emerald">
    <div class="kpi-label">Ingresos</div>
    <div class="kpi-valor emerald">{{ ingresos_fmt }}</div>
    {% if delta_ingresos %}
    <div class="kpi-delta {{ 'emerald' if delta_ingresos > 0 else 'coral' }}">
      {{ '↑' if delta_ingresos > 0 else '↓' }} {{ delta_ingresos|abs|round(1) }}% vs mes anterior
    </div>
    {% endif %}
  </div>
  <div class="kpi-card coral">
    <div class="kpi-label">Gastos</div>
    <div class="kpi-valor coral">{{ gastos_fmt }}</div>
  </div>
  <div class="kpi-card emerald">
    <div class="kpi-label">Utilidad neta</div>
    <div class="kpi-valor">{{ utilidad_fmt }}</div>
  </div>
  <div class="kpi-card amber">
    <div class="kpi-label">Margen</div>
    <div class="kpi-valor amber">{{ margen }}%</div>
  </div>
</div>

<div class="section-title">Análisis visual</div>
<div class="charts-row">
  <div class="chart-card">
    <div style="font-size:11px; color:#6B7A8D; margin-bottom:8px;">Ingresos vs Gastos — últimos 6 meses</div>
    <img src="data:image/png;base64,{{ grafica_barras }}" />
  </div>
  <div class="chart-card">
    <div style="font-size:11px; color:#6B7A8D; margin-bottom:8px;">Composición de gastos</div>
    <img src="data:image/png;base64,{{ grafica_donut }}" />
  </div>
</div>

{% if categorias %}
<div class="section-title">Categorías de ingreso</div>
<div class="table-card">
  <table>
    <thead>
      <tr><th>Categoría</th><th>Valor</th><th>% del total</th></tr>
    </thead>
    <tbody>
      {% for cat in categorias %}
      <tr>
        <td>{{ cat.nombre }}</td>
        <td class="emerald">{{ cat.valor_fmt }}</td>
        <td style="color:#6B7A8D;">{{ cat.pct }}%</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endif %}

{% if analisis %}
<div class="section-title">✦ Análisis con IA</div>
<div class="ai-card">
  <div class="ai-resumen">{{ analisis.resumen }}</div>
  {% for alerta in analisis.alertas %}
  <div class="alerta {{ alerta.tipo }}">{{ alerta.mensaje }}</div>
  {% endfor %}
  {% if analisis.recomendacion_principal %}
  <div class="recomendacion">
    <strong>Recomendación:</strong> {{ analisis.recomendacion_principal }}
  </div>
  {% endif %}
</div>
{% endif %}

<div class="footer">
  <span>FinPyme · Dashboard financiero con IA para pymes colombianas</span>
  <span>Generado el {{ fecha_generacion }}</span>
</div>

</body>
</html>
"""
