from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course, Module, Topic
from app.models.question import Option, Question
from app.models.user import User


def _assert_owner_or_admin(user: User, instructor_id: uuid.UUID | None) -> None:
    if user.role == "admin":
        return
    if instructor_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own courses",
        )


async def assert_can_manage_course(
    db: AsyncSession,
    user: User,
    course_id: uuid.UUID,
) -> None:
    result = await db.execute(select(Course.id, Course.instructor_id).where(Course.id == course_id))
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    _assert_owner_or_admin(user, row.instructor_id)


async def assert_can_manage_module(
    db: AsyncSession,
    user: User,
    module_id: uuid.UUID,
) -> None:
    result = await db.execute(
        select(Module.id, Course.instructor_id)
        .join(Module, Module.course_id == Course.id)
        .where(Module.id == module_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    _assert_owner_or_admin(user, row.instructor_id)


async def assert_can_manage_topic(
    db: AsyncSession,
    user: User,
    topic_id: uuid.UUID,
) -> None:
    result = await db.execute(
        select(Topic.id, Course.instructor_id)
        .join(Module, Module.course_id == Course.id)
        .join(Topic, Topic.module_id == Module.id)
        .where(Topic.id == topic_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    _assert_owner_or_admin(user, row.instructor_id)


async def assert_can_manage_question(
    db: AsyncSession,
    user: User,
    question_id: uuid.UUID,
) -> None:
    topic_result = await db.execute(
        select(Question.id, Course.instructor_id)
        .join(Module, Module.course_id == Course.id)
        .join(Topic, Topic.module_id == Module.id)
        .join(Question, Question.topic_id == Topic.id)
        .where(Question.id == question_id)
    )
    row = topic_result.one_or_none()
    if row is None:
        module_result = await db.execute(
            select(Question.id, Course.instructor_id)
            .join(Module, Module.course_id == Course.id)
            .join(Question, Question.module_id == Module.id)
            .where(Question.id == question_id)
        )
        row = module_result.one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    _assert_owner_or_admin(user, row.instructor_id)


async def assert_can_manage_option(
    db: AsyncSession,
    user: User,
    option_id: uuid.UUID,
) -> None:
    result = await db.execute(select(Option.question_id).where(Option.id == option_id))
    question_id = result.scalar_one_or_none()
    if question_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Option not found")
    await assert_can_manage_question(db, user, question_id)
