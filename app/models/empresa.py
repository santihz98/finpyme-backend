from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid

from app.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nombre: Mapped[str] = mapped_column(String(200))
    nit: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ciudad: Mapped[str] = mapped_column(String(100))
    sector: Mapped[str] = mapped_column(String(50))   # restaurante|distribuidora|clinica|otro
    plan: Mapped[str] = mapped_column(String(20), default="free")  # free|starter|pro
    activo: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    usuarios: Mapped[list["Usuario"]] = relationship(  # noqa: F821
        "Usuario", back_populates="empresa", cascade="all, delete-orphan"
    )
    periodos: Mapped[list["PeriodoFinanciero"]] = relationship(  # noqa: F821
        "PeriodoFinanciero", back_populates="empresa", cascade="all, delete-orphan"
    )
    analisis: Mapped[list["AnalisisIA"]] = relationship(  # noqa: F821
        "AnalisisIA", back_populates="empresa", cascade="all, delete-orphan"
    )
