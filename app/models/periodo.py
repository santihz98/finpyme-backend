from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Periodo(Base):
    __tablename__ = "periodos"
    __table_args__ = (
        Index("ix_periodos_empresa_periodo", "empresa_id", "periodo", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    # "2025-01"
    periodo: Mapped[str] = mapped_column(String(7))

    # Denormalized KPIs for fast list reads
    ingresos_total: Mapped[float] = mapped_column(Numeric(18, 2))
    gastos_total: Mapped[float] = mapped_column(Numeric(18, 2))
    utilidad_neta: Mapped[float] = mapped_column(Numeric(18, 2))
    margen_pct: Mapped[float] = mapped_column(Numeric(6, 2))

    # Full month detail: ingresos por categoría, composición gastos, anomalía
    data_json: Mapped[dict] = mapped_column(JSON)

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
    analisis: Mapped[list["Analisis"]] = relationship(  # noqa: F821
        "Analisis", back_populates="periodo"
    )
