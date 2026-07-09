from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    nit: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ciudad: Mapped[str] = mapped_column(String(100))
    sector: Mapped[str] = mapped_column(String(100))
    activa: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    usuarios: Mapped[list["Usuario"]] = relationship(  # noqa: F821
        "Usuario", back_populates="empresa"
    )
    periodos: Mapped[list["Periodo"]] = relationship(  # noqa: F821
        "Periodo", back_populates="empresa"
    )
    analisis: Mapped[list["Analisis"]] = relationship(  # noqa: F821
        "Analisis", back_populates="empresa"
    )
