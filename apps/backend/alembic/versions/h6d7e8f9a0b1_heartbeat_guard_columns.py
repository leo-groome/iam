"""heartbeat guard columns (IAM-005)

Revision ID: h6d7e8f9a0b1
Revises: g5c6d7e8f9a0
"""

import sqlalchemy as sa
from alembic import op

revision = "h6d7e8f9a0b1"
down_revision = "g5c6d7e8f9a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content_blocks", sa.Column("pdf_total_pages", sa.Integer(), nullable=True))
    op.add_column(
        "content_block_progress",
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_block_progress", "last_heartbeat_at")
    op.drop_column("content_blocks", "pdf_total_pages")
