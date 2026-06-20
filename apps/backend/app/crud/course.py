from __future__ import annotations

import base64
import uuid
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import Course, Module
from app.models.progress import Enrollment
from app.models.user import User


def _user_age(user: User) -> int:
    today = date.today()
    b = user.birth_date
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))


def _encode_cursor(order_index: int, course_id: uuid.UUID) -> str:
    raw = f"{order_index}:{course_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[int, uuid.UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    idx_str, id_str = raw.split(":", 1)
    return int(idx_str), uuid.UUID(id_str)


async def get_courses_for_user(
    db: AsyncSession,
    user: User,
    cursor: str | None,
    limit: int,
) -> tuple[list[Course], str | None]:
    age = _user_age(user)

    enrolled_subq = (
        select(Enrollment.course_id).where(Enrollment.user_id == user.id).scalar_subquery()
    )

    age_eligible = or_(
        Course.age_min.is_(None),
        Course.age_min <= age,
    )
    age_max_ok = or_(
        Course.age_max.is_(None),
        Course.age_max >= age,
    )

    stmt = (
        select(Course)
        .where(
            or_(
                (Course.status == "publicado") & age_eligible & age_max_ok,
                (Course.status == "archivado") & (Course.id.in_(enrolled_subq)),
            )
        )
        .order_by(Course.order_index, Course.id)
    )

    if cursor:
        idx, cid = _decode_cursor(cursor)
        stmt = stmt.where(
            (Course.order_index > idx)
            | ((Course.order_index == idx) & (Course.id > cid))
        )

    stmt = stmt.limit(limit + 1)

    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    next_cursor: str | None = None
    if len(rows) > limit:
        rows = rows[:limit]
        last = rows[-1]
        next_cursor = _encode_cursor(last.order_index, last.id)

    return rows, next_cursor


async def get_course_by_slug(db: AsyncSession, slug: str) -> Course | None:
    stmt = (
        select(Course)
        .where(Course.slug == slug)
        .options(
            selectinload(Course.modules).selectinload(Module.topics)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def is_course_eligible_for_user(course: Course, user: User, enrolled: bool) -> bool:
    if course.status == "archivado":
        return enrolled
    if course.status != "publicado":
        return False
    age = _user_age(user)
    if course.age_min is not None and age < course.age_min:
        return False
    return course.age_max is None or age <= course.age_max
