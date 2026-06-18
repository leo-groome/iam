from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import Module, Topic
from app.models.progress import TopicProgress
from app.models.user import User


async def get_topic_with_module(db: AsyncSession, topic_id: uuid.UUID) -> Topic | None:
    stmt = (
        select(Topic)
        .where(Topic.id == topic_id)
        .options(selectinload(Topic.module).selectinload(Module.topics))
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
