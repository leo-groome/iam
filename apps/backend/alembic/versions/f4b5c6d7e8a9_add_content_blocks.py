"""add content_blocks and content_block_progress

Revision ID: f4b5c6d7e8a9
Revises: e3a4b5c6d7e8
Create Date: 2026-08-04

Introduces multi-block content per topic. `topics` keeps its existing
content_type/content_body/media_key/duration_seconds columns (untouched,
future cleanup) but the new `content_blocks` table becomes the source of
truth going forward.

Data migration:
- For every existing topic, create a "primary" block (order_index=0) with
  kind=topics.content_type, media_key=topics.media_key,
  duration_seconds=topics.duration_seconds, and content_body only when
  content_type='texto' (otherwise NULL).
- If a non-texto topic also has a non-empty content_body (e.g. a video topic
  with accompanying notes), create a secondary block (order_index=1,
  kind='texto') carrying that content_body.
- Existing topic_progress rows are ported to content_block_progress, linked
  to each topic's primary block (order_index=0).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f4b5c6d7e8a9"
down_revision: Union[str, None] = "e3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("media_key", sa.Text(), nullable=True),
        sa.Column("content_body", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "kind IN ('video', 'pdf', 'imagen', 'texto', 'audio')",
            name="ck_content_blocks_kind",
        ),
    )
    op.create_index("ix_content_blocks_topic_order", "content_blocks", ["topic_id", "order_index"])

    op.create_table(
        "content_block_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "block_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_blocks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("video_last_pos_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("video_max_seen_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pdf_last_page", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pdf_total_pages", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "block_id", name="uq_content_block_progress_user_block"),
    )

    # --- Data migration -------------------------------------------------
    # 1. Primary block (order_index=0) per topic.
    op.execute(
        """
        INSERT INTO content_blocks
            (id, topic_id, kind, media_key, content_body, duration_seconds, order_index, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            t.id,
            t.content_type,
            t.media_key,
            CASE WHEN t.content_type = 'texto' THEN t.content_body ELSE NULL END,
            t.duration_seconds,
            0,
            now(),
            now()
        FROM topics t
        """
    )

    # 2. Secondary texto block (order_index=1) for non-texto topics that also
    #    carry a non-empty content_body (e.g. notes attached to a video).
    op.execute(
        """
        INSERT INTO content_blocks
            (id, topic_id, kind, media_key, content_body, duration_seconds, order_index, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            t.id,
            'texto',
            NULL,
            t.content_body,
            NULL,
            1,
            now(),
            now()
        FROM topics t
        WHERE t.content_type <> 'texto'
          AND t.content_body IS NOT NULL
          AND t.content_body <> ''
        """
    )

    # 3. Port topic_progress -> content_block_progress, linked to each
    #    topic's primary block (order_index=0).
    op.execute(
        """
        INSERT INTO content_block_progress
            (id, user_id, block_id, video_last_pos_seconds, video_max_seen_pct,
             pdf_last_page, pdf_total_pages, completed_at, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            tp.user_id,
            cb.id,
            tp.video_last_pos_seconds,
            tp.video_max_seen_pct,
            tp.pdf_last_page,
            tp.pdf_total_pages,
            tp.content_completed_at,
            now(),
            now()
        FROM topic_progress tp
        JOIN content_blocks cb ON cb.topic_id = tp.topic_id AND cb.order_index = 0
        """
    )


def downgrade() -> None:
    op.drop_table("content_block_progress")
    op.drop_index("ix_content_blocks_topic_order", table_name="content_blocks")
    op.drop_table("content_blocks")
