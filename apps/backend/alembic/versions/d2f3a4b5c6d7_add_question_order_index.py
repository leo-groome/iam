"""add question order index

Revision ID: d2f3a4b5c6d7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-27
"""

import sqlalchemy as sa

from alembic import op

revision = "d2f3a4b5c6d7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_questions_topic_order", "questions", ["topic_id", "order_index"])
    op.create_index("ix_questions_module_order", "questions", ["module_id", "order_index"])


def downgrade() -> None:
    op.drop_index("ix_questions_module_order", table_name="questions")
    op.drop_index("ix_questions_topic_order", table_name="questions")
    op.drop_column("questions", "order_index")
