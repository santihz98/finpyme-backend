from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AnalisisIA(Base):
    __tablename__ = "analisis_ia"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    empresa_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("empresas.id"), index=True)
    periodo_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("periodos_financieros.id"), index=True
    )

    resumen: Mapped[str] = mapped_column(Text)
    alertas_json: Mapped[list] = mapped_column(JSON)  # [{"tipo": ..., "mensaje": ...}]
    recomendacion: Mapped[str] = mapped_column(Text)

    modelo_usado: Mapped[str] = mapped_column(String(100), default="claude-sonnet-4-6")
    tokens_usados: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    empresa: Mapped["Empresa"] = relationship(  # noqa: F821
        "Empresa", back_populates="analisis"
    )
    periodo: Mapped["PeriodoFinanciero"] = relationship(  # noqa: F821
        "PeriodoFinanciero", back_populates="analisis"
    )
