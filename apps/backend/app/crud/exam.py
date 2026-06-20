from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.progress import ExamAttempt
from app.models.question import Question


async def get_questions_for_topic(db: AsyncSession, topic_id: uuid.UUID) -> list[Question]:
    stmt = (
        select(Question)
        .where(Question.topic_id == topic_id, Question.archived_at.is_(None))
        .options(selectinload(Question.options))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_questions_for_module(db: AsyncSession, module_id: uuid.UUID) -> list[Question]:
    stmt = (
        select(Question)
        .where(Question.module_id == module_id, Question.archived_at.is_(None))
        .options(selectinload(Question.options))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def save_attempt(
    db: AsyncSession,
    user_id: uuid.UUID,
    topic_id: uuid.UUID | None,
    module_id: uuid.UUID | None,
    score: int,
    passed: bool,
    min_score_snapshot: int,
    answers: dict[str, str],
) -> ExamAttempt:
    attempt = ExamAttempt(
        user_id=user_id,
        topic_id=topic_id,
        module_id=module_id,
        score=score,
        passed=passed,
        min_score_snapshot=min_score_snapshot,
        answers=answers,
        created_at=datetime.now(UTC),
    )
    db.add(attempt)
    await db.flush()
    return attempt


async def count_consecutive_failures(
    db: AsyncSession, user_id: uuid.UUID, topic_id: uuid.UUID
) -> int:
    stmt = (
        select(ExamAttempt)
        .where(ExamAttempt.user_id == user_id, ExamAttempt.topic_id == topic_id)
        .order_by(ExamAttempt.created_at.desc())
    )
    result = await db.execute(stmt)
    attempts = list(result.scalars().all())
    count = 0
    for attempt in attempts:
        if not attempt.passed:
            count += 1
        else:
            break
    return count
