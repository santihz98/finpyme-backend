from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PeriodoFinanciero(Base):
    __tablename__ = "periodos_financieros"
    __table_args__ = (
        Index("ix_periodos_financieros_empresa_periodo", "empresa_id", "periodo", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    empresa_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("empresas.id"), index=True)
    periodo: Mapped[str] = mapped_column(String(7))  # "2025-01"
    fuente: Mapped[str] = mapped_column(String(20), default="manual")  # manual|csv|api

    # Full month detail: ingresos por categoría, composición gastos, anomalía
    datos_json: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    empresa: Mapped["Empresa"] = relationship(  # noqa: F821
        "Empresa", back_populates="periodos"
    )
    analisis: Mapped[list["AnalisisIA"]] = relationship(  # noqa: F821
        "AnalisisIA", back_populates="periodo"
    )
