"""create initial tables

Revision ID: 0001
Revises:
Create Date: 2026-07-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "empresas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("nit", sa.String(20), nullable=False),
        sa.Column("ciudad", sa.String(100), nullable=False),
        sa.Column("sector", sa.String(50), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_empresas_nit", "empresas", ["nit"], unique=True)

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False, server_default="owner"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ultimo_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usuarios_empresa_id", "usuarios", ["empresa_id"])
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "periodos_financieros",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("fuente", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("datos_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_periodos_financieros_empresa_id", "periodos_financieros", ["empresa_id"])
    op.create_index(
        "ix_periodos_financieros_empresa_periodo",
        "periodos_financieros",
        ["empresa_id", "periodo"],
        unique=True,
    )

    op.create_table(
        "analisis_ia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("empresa_id", sa.Uuid(), nullable=False),
        sa.Column("periodo_id", sa.Uuid(), nullable=False),
        sa.Column("resumen", sa.Text(), nullable=False),
        sa.Column("alertas_json", sa.JSON(), nullable=False),
        sa.Column("recomendacion", sa.Text(), nullable=False),
        sa.Column("modelo_usado", sa.String(100), nullable=False, server_default="claude-sonnet-4-6"),
        sa.Column("tokens_usados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["periodo_id"], ["periodos_financieros.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analisis_ia_empresa_id", "analisis_ia", ["empresa_id"])
    op.create_index("ix_analisis_ia_periodo_id", "analisis_ia", ["periodo_id"])


def downgrade() -> None:
    op.drop_table("analisis_ia")
    op.drop_table("periodos_financieros")
    op.drop_table("usuarios")
    op.drop_table("empresas")
