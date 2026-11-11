"""Persist exam attempt limits and optional answer feedback.

Revision ID: g5c6d7e8f9a0
Revises: f4b5c6d7e8a9
"""
import sqlalchemy as sa

from alembic import op

revision = "g5c6d7e8f9a0"
down_revision = "f4b5c6d7e8a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("modules", "topics"):
        op.add_column(table, sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"))
        op.create_check_constraint(f"ck_{table}_max_attempts", table, "max_attempts BETWEEN 1 AND 10")
    op.add_column("options", sa.Column("feedback", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("options", "feedback")
    for table in ("topics", "modules"):
        op.drop_constraint(f"ck_{table}_max_attempts", table, type_="check")
        op.drop_column(table, "max_attempts")
