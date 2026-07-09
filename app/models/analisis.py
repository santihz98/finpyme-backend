from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Analisis(Base):
    __tablename__ = "analisis"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    periodo_id: Mapped[int] = mapped_column(ForeignKey("periodos.id"), index=True)

    resumen: Mapped[str] = mapped_column(Text)
    alertas: Mapped[list] = mapped_column(JSON)  # [{"tipo": ..., "mensaje": ...}]
    recomendacion: Mapped[str] = mapped_column(Text)

    modelo: Mapped[str] = mapped_column(String(100), default="claude-sonnet-4-6")
    tokens_usados: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    empresa: Mapped["Empresa"] = relationship(  # noqa: F821
        "Empresa", back_populates="analisis"
    )
    periodo: Mapped["Periodo"] = relationship(  # noqa: F821
        "Periodo", back_populates="analisis"
    )
