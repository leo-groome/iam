"""add audio to topics content_type check constraint

Revision ID: e3a4b5c6d7e8
Revises: d2f3a4b5c6d7
Create Date: 2026-07-09
"""

from alembic import op

revision = "e3a4b5c6d7e8"
down_revision = "d2f3a4b5c6d7"
branch_labels = None
depends_on = None

_CONSTRAINT = "ck_topics_content_type"
_NEW = "content_type IN ('video', 'pdf', 'imagen', 'texto', 'audio')"
_OLD = "content_type IN ('video', 'pdf', 'imagen', 'texto')"


def upgrade() -> None:
    op.drop_constraint(_CONSTRAINT, "topics", type_="check")
    op.create_check_constraint(_CONSTRAINT, "topics", _NEW)


def downgrade() -> None:
    op.drop_constraint(_CONSTRAINT, "topics", type_="check")
    op.create_check_constraint(_CONSTRAINT, "topics", _OLD)
