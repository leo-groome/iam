"""add onboarding_responses

Revision ID: a1b2c3d4e5f6
Revises: c92e06fd8e9f
Create Date: 2026-06-26 00:00:00.000000

1:1 with users (UNIQUE user_id). Structured demographic columns + JSONB `extra`
for future dynamic survey questions. CHECK constraints mirror the Pydantic enums.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "c92e06fd8e9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "onboarding_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("edad", sa.String(10), nullable=False),
        sa.Column("sexo", sa.String(10), nullable=False),
        sa.Column("diocesis", sa.String(200), nullable=False),
        sa.Column("ciudad", sa.String(200), nullable=False),
        sa.Column("parroquia", sa.String(200), nullable=False),
        sa.Column("entorno", sa.String(10), nullable=False),
        sa.Column("pastoral", sa.String(20), nullable=False),
        sa.Column("extra", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", name="uq_onboarding_user"),
        sa.CheckConstraint("sexo IN ('Hombre', 'Mujer')", name="ck_onboarding_sexo"),
        sa.CheckConstraint(
            "edad IN ('<18', '18-25', '26-35', '36-50', '>50')", name="ck_onboarding_edad"
        ),
        sa.CheckConstraint("entorno IN ('Rural', 'Urbana')", name="ck_onboarding_entorno"),
        sa.CheckConstraint(
            "pastoral IN ('IAM', 'Catequesis', 'Juvenil', 'Familiar', 'Otra')",
            name="ck_onboarding_pastoral",
        ),
    )
    op.create_index("ix_onboarding_user", "onboarding_responses", ["user_id"])
    op.create_index("ix_onboarding_diocesis", "onboarding_responses", ["diocesis"])
    op.create_index("ix_onboarding_parroquia", "onboarding_responses", ["parroquia"])
    op.create_index("ix_onboarding_pastoral", "onboarding_responses", ["pastoral"])
    op.create_index("ix_onboarding_entorno", "onboarding_responses", ["entorno"])


def downgrade() -> None:
    op.drop_table("onboarding_responses")
