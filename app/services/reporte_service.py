import base64
import io
from datetime import datetime

import matplotlib
import matplotlib.patches as mpatches
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

    def _generar_grafica_barras(self, meses: list) -> str:
        """Barras de ingresos vs gastos por mes. Retorna PNG en base64."""
        fig, ax = plt.subplots(figsize=(8, 3))
        fig.patch.set_facecolor(self.colores["slate"])
        ax.set_facecolor(self.colores["slate"])

        if meses:
            labels = [m.get("periodo", "") for m in meses]
            ingresos = [m.get("ingresos_total", 0) for m in meses]
            gastos = [m.get("gastos_total", 0) for m in meses]
            x = range(len(labels))
            w = 0.35
            ax.bar([i - w / 2 for i in x], ingresos, w,
                   color=self.colores["emerald"], label="Ingresos")
            ax.bar([i + w / 2 for i in x], gastos, w,
                   color=self.colores["coral"], label="Gastos")
            ax.set_xticks(list(x))
            ax.set_xticklabels(labels, color=self.colores["pearl"], fontsize=7)
        else:
            ax.text(0.5, 0.5, "Sin datos de tendencia",
                    ha="center", va="center", color=self.colores["muted"],
                    transform=ax.transAxes)

        ax.tick_params(colors=self.colores["pearl"])
        ax.spines[:].set_color(self.colores["muted"])
        legend = ax.legend(facecolor=self.colores["ink"],
                           labelcolor=self.colores["pearl"], fontsize=8)
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=self.colores["slate"])
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode()

    def _generar_grafica_donut(self, gastos: dict) -> str:
        """Donut de composición de gastos. Retorna PNG en base64."""
        fig, ax = plt.subplots(figsize=(4, 4))
        fig.patch.set_facecolor(self.colores["slate"])
        ax.set_facecolor(self.colores["slate"])

        excluir = {"total"}
        categorias = {k: v for k, v in gastos.items()
                      if k not in excluir and isinstance(v, (int, float)) and v > 0}

        if categorias:
            palette = [self.colores["emerald"], self.colores["amber"],
                       self.colores["coral"], self.colores["muted"],
                       self.colores["pearl"]]
            colores = (palette * ((len(categorias) // len(palette)) + 1))[:len(categorias)]
            wedges, _ = ax.pie(
                list(categorias.values()),
                colors=colores,
                wedgeprops={"width": 0.5, "edgecolor": self.colores["slate"]},
                startangle=90,
            )
            patches = [mpatches.Patch(color=c, label=k)
                       for k, c in zip(categorias.keys(), colores)]
            ax.legend(handles=patches, loc="lower center",
                      bbox_to_anchor=(0.5, -0.15), ncol=2,
                      facecolor=self.colores["ink"],
                      labelcolor=self.colores["pearl"], fontsize=7)
        else:
            ax.text(0.5, 0.5, "Sin datos de gastos",
                    ha="center", va="center", color=self.colores["muted"],
                    transform=ax.transAxes)

        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=self.colores["slate"])
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode()

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
