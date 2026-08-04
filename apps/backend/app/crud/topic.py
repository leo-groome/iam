from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import ContentBlock, Module, Topic
from app.models.progress import ContentBlockProgress, TopicProgress
from app.models.user import User

if TYPE_CHECKING:
    from app.schemas.admin.topics import ContentBlockIn


async def get_topic_with_module(db: AsyncSession, topic_id: uuid.UUID) -> Topic | None:
    stmt = (
        select(Topic)
        .where(Topic.id == topic_id)
        .options(
            selectinload(Topic.module).selectinload(Module.topics),
            selectinload(Topic.blocks),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_progress(
    db: AsyncSession, user: User, topic: Topic
) -> TopicProgress:
    stmt = select(TopicProgress).where(
        TopicProgress.user_id == user.id,
        TopicProgress.topic_id == topic.id,
    )
    result = await db.execute(stmt)
    tp = result.scalar_one_or_none()
    if tp is None:
        tp = TopicProgress(
            user_id=user.id,
            topic_id=topic.id,
            state="bloqueado",
        )
        db.add(tp)
        await db.flush()
    return tp


async def get_or_create_block_progress(
    db: AsyncSession, user: User, block: ContentBlock
) -> ContentBlockProgress:
    stmt = select(ContentBlockProgress).where(
        ContentBlockProgress.user_id == user.id,
        ContentBlockProgress.block_id == block.id,
    )
    result = await db.execute(stmt)
    bp = result.scalar_one_or_none()
    if bp is None:
        bp = ContentBlockProgress(
            user_id=user.id,
            block_id=block.id,
        )
        db.add(bp)
        await db.flush()
    return bp


async def replace_topic_blocks(
    db: AsyncSession, topic: Topic, blocks_in: list[ContentBlockIn]
) -> None:
    """Replace all content blocks of a topic with a new ordered set.

    Deletes existing blocks (and their per-user progress rows — done explicitly
    rather than relying on DB-level ON DELETE CASCADE, since SQLite in tests
    does not enforce FK actions by default) and creates the new ones with
    sequential order_index. Syncs topic.content_type to the first block's kind.
    Caller is responsible for ensuring blocks_in is non-empty.

    Also re-gates in-progress students: since ContentBlockProgress for the old
    blocks is wiped, a student who was 'contenido_visto' or 'en_repaso' would
    otherwise keep their exam unlocked over content they never saw (the new
    blocks). All TopicProgress rows for this topic in those two states are
    reset to 'disponible' with content_completed_at=None, forcing them back
    through the (new) content before the exam re-unlocks. 'aprobado' rows are
    left untouched — the exam was already passed and that history is respected.
    'bloqueado' rows are left as-is (still locked, nothing to re-gate). All of
    this runs in the same transaction as the block replacement — caller commits.
    """
    old_block_ids = [b.id for b in topic.blocks]
    if old_block_ids:
        await db.execute(
            delete(ContentBlockProgress).where(ContentBlockProgress.block_id.in_(old_block_ids))
        )
        await db.execute(delete(ContentBlock).where(ContentBlock.id.in_(old_block_ids)))

    for idx, block_in in enumerate(blocks_in):
        db.add(
            ContentBlock(
                topic_id=topic.id,
                kind=block_in.kind,
                media_key=block_in.media_key,
                content_body=block_in.content_body,
                duration_seconds=block_in.duration_seconds,
                order_index=idx,
            )
        )

    topic.content_type = blocks_in[0].kind

    await db.execute(
        update(TopicProgress)
        .where(
            TopicProgress.topic_id == topic.id,
            TopicProgress.state.in_(("contenido_visto", "en_repaso")),
        )
        .values(state="disponible", content_completed_at=None)
    )

    await db.flush()
