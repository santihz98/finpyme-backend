import base64

import resend

from app.config import settings
from app.services.reporte_service import ReporteService


class EmailService:

    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY
        self.reporte_service = ReporteService()

    async def enviar_reporte_mensual(
        self,
        email_destino: str,
        nombre_usuario: str,
        empresa: dict,
        mes_data: dict,
        mes_anterior: dict | None,
        analisis: dict | None,
        periodos_resumen: list,
        grafica_barras: str,
        grafica_donut: str,
    ) -> bool:
        try:
            pdf_bytes = await self.reporte_service.generar_pdf(
                empresa=empresa,
                mes_data=mes_data,
                mes_anterior=mes_anterior,
                analisis=analisis,
                periodos_resumen=periodos_resumen,
                grafica_barras=grafica_barras,
                grafica_donut=grafica_donut,
            )

            periodo = mes_data["periodo"]
            año, mes = periodo.split("-")
            meses = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
            ]
            mes_label = f"{meses[int(mes) - 1]} {año}"

            html_email = self._html_email(nombre_usuario, empresa["nombre"], mes_label)

            nombre_archivo = f"reporte-finpyme-{periodo}.pdf"
            pdf_b64 = base64.b64encode(pdf_bytes).decode()

            params = {
                "from": f"FinPyme <{settings.EMAIL_FROM}>",
                "to": [email_destino],
                "subject": f"Tu reporte financiero de {mes_label} — {empresa['nombre']}",
                "html": html_email,
                "attachments": [{
                    "filename": nombre_archivo,
                    "content": pdf_b64,
                }],
            }

            resend.Emails.send(params)
            return True

        except Exception as e:
            print(f"Error enviando email: {e}")
            return False

    def _html_email(self, nombre: str, empresa: str, mes_label: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; background: #f4f4f4;
                     padding: 32px; color: #333;">
          <div style="max-width: 560px; margin: 0 auto;
                      background: #0F1923; border-radius: 12px;
                      padding: 32px; color: #E8EDF2;">
            <div style="font-size: 22px; font-weight: 700; margin-bottom: 8px;">
              Fin<span style="color: #00C896;">Pyme</span>
            </div>
            <p style="color: #6B7A8D; font-size: 13px; margin-bottom: 24px;">
              Dashboard financiero con IA
            </p>
            <p style="font-size: 15px;">Hola {nombre},</p>
            <p style="font-size: 13px; color: #6B7A8D; line-height: 1.6; margin: 12px 0;">
              Tu reporte financiero de <strong style="color: #E8EDF2;">
              {mes_label}</strong> para <strong style="color: #E8EDF2;">
              {empresa}</strong> está listo.
            </p>
            <p style="font-size: 13px; color: #6B7A8D; line-height: 1.6;">
              Encuentra el PDF adjunto con el análisis completo de ingresos,
              gastos, márgenes y recomendaciones.
            </p>
            <div style="margin: 24px 0; padding: 16px; background: #1A2A3A;
                        border-radius: 8px; border-left: 3px solid #00C896;">
              <p style="font-size: 12px; color: #6B7A8D; margin: 0;">
                Este reporte fue generado automáticamente por FinPyme.
                Si tienes preguntas, responde a este correo.
              </p>
            </div>
            <p style="font-size: 11px; color: #6B7A8D; margin-top: 24px;">
              FinPyme · Dashboard financiero para pymes colombianas
            </p>
          </div>
        </body>
        </html>
        """
