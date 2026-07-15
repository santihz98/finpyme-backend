# Import all models here so Alembic autogenerate can detect them
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.periodo import PeriodoFinanciero
from app.models.analisis import AnalisisIA

__all__ = ["Empresa", "Usuario", "PeriodoFinanciero", "AnalisisIA"]
