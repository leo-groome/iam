from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.course import (
    get_course_by_slug,
    get_courses_for_user,
    is_course_eligible_for_user,
)
from app.db import get_db
from app.deps import get_current_user
from app.models.course import Module
from app.models.progress import Enrollment, TopicProgress
from app.models.user import User
from app.schemas.course import (
    CourseCard,
    CourseCardListResponse,
    CourseDetail,
    EnrollResponse,
    ModuleItem,
    ModuleTopicItem,
)
from app.schemas.topic import CourseProgressResponse, ModuleProgressItem, TopicStateItem
from app.services.progress_engine import compute_topic_state

router = APIRouter(prefix="/courses", tags=["catalog"])


def _build_module_item(m: Module) -> ModuleItem:
    active_topics = sorted(
        [t for t in m.topics if t.archived_at is None],
        key=lambda t: t.order_index,
    )
    return ModuleItem(
        id=m.id,
        title=m.title,
        order_index=m.order_index,
        topics=[
            ModuleTopicItem(
                id=t.id,
                title=t.title,
                content_type=t.content_type,
                duration_seconds=t.duration_seconds,
                has_exam=t.has_exam,
                order_index=t.order_index,
            )
            for t in active_topics
        ],
    )


@router.get("", response_model=CourseCardListResponse)
async def list_courses(
    cursor: str | None = Query(None),
    limit: int = Query(12, ge=1, le=50),
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> CourseCardListResponse:
    courses, next_cursor = await get_courses_for_user(db, current_user, cursor, limit)
    return CourseCardListResponse(
        items=[CourseCard.model_validate(c) for c in courses],
        next_cursor=next_cursor,
    )


@router.get("/{slug}", response_model=CourseDetail)
async def get_course_detail(
    slug: str,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> CourseDetail:
    course = await get_course_by_slug(db, slug)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrollment_result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course.id,
        )
    )
    enrollment = enrollment_result.scalar_one_or_none()
    enrolled = enrollment is not None

    eligible = await is_course_eligible_for_user(course, current_user, enrolled)
    if not eligible:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if enrollment is None:
        enrollment_status = "no_iniciado"
        progress_pct = 0
    elif enrollment.completed_at is not None:
        enrollment_status = "completado"
        progress_pct = enrollment.progress_cached
    else:
        enrollment_status = "en_progreso"
        progress_pct = enrollment.progress_cached

    active_modules = sorted(
        [m for m in course.modules if m.archived_at is None],
        key=lambda m: m.order_index,
    )

    return CourseDetail(
        id=course.id,
        slug=course.slug,
        title=course.title,
        short_desc=course.short_desc,
        long_desc=course.long_desc,
        cover_key=course.cover_key,
        age_min=course.age_min,
        age_max=course.age_max,
        order_index=course.order_index,
        status=course.status,
        modules=[_build_module_item(m) for m in active_modules],
        enrollment_status=enrollment_status,
        progress_pct=progress_pct,
    )


@router.post("/{slug}/enroll", response_model=EnrollResponse)
async def enroll_course(
    slug: str,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> EnrollResponse:
    course = await get_course_by_slug(db, slug)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrollment_result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course.id,
        )
    )
    existing = enrollment_result.scalar_one_or_none()

    if existing is not None:
        return EnrollResponse(
            id=existing.id,
            user_id=existing.user_id,
            course_id=existing.course_id,
            progress_cached=existing.progress_cached,
        )

    eligible = await is_course_eligible_for_user(course, current_user, False)
    if not eligible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not eligible for this course"
        )

    enrollment = Enrollment(
        user_id=current_user.id,
        course_id=course.id,
        started_at=datetime.now(UTC),
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)

    return EnrollResponse(
        id=enrollment.id,
        user_id=enrollment.user_id,
        course_id=enrollment.course_id,
        progress_cached=enrollment.progress_cached,
    )


@router.get("/{slug}/progress", response_model=CourseProgressResponse)
async def get_course_progress(
    slug: str,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> CourseProgressResponse:
    course = await get_course_by_slug(db, slug)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrollment_result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course.id,
        )
    )
    enrollment = enrollment_result.scalar_one_or_none()
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enrolled")

    active_modules = sorted(
        [m for m in course.modules if m.archived_at is None],
        key=lambda m: m.order_index,
    )

    module_items: list[ModuleProgressItem] = []
    total = 0
    approved = 0

    for m in active_modules:
        active_topics = sorted(
            [t for t in m.topics if t.archived_at is None],
            key=lambda t: t.order_index,
        )
        topic_states: list[TopicStateItem] = []
        module_approved_count = 0

        for t in active_topics:
            total += 1
            state = await compute_topic_state(db, current_user, t)
            tp_result = await db.execute(
                select(TopicProgress).where(
                    TopicProgress.user_id == current_user.id,
                    TopicProgress.topic_id == t.id,
                )
            )
            tp = tp_result.scalar_one_or_none()
            real_state = tp.state if tp is not None else state
            if real_state == "aprobado":
                approved += 1
                module_approved_count += 1
            topic_states.append(TopicStateItem(id=t.id, state=real_state))

        mod_status = "aprobado" if module_approved_count == len(active_topics) else "en_progreso"
        module_items.append(
            ModuleProgressItem(id=m.id, status=mod_status, topics=topic_states)
        )

    course_pct = int((approved / total) * 100) if total > 0 else 0

    return CourseProgressResponse(course_pct=course_pct, modules=module_items)
