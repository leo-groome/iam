"""Admin students router — admin-only.

Registration line for routers/__init__.py:
    from .admin.students import router as admin_students_router
    api_router.include_router(admin_students_router)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import admin as crud
from app.db import get_db
from app.deps import require_role
from app.models.user import User
from app.schemas.admin.students import StudentDetail, StudentListItem, StudentListResponse

router = APIRouter(prefix="/api/v1/admin/students", tags=["admin-students"])

_guard = require_role("admin")


@router.get("", response_model=StudentListResponse)
async def list_students(
    q: str | None = Query(None, min_length=2),
    student_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> StudentListResponse:
    rows, total = await crud.list_students(db, q, student_status, page, page_size)
    items = [
        StudentListItem(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            created_at=user.created_at,  # type: ignore[arg-type]
            is_stuck=is_stuck,
        )
        for user, is_stuck in rows
    ]
    return StudentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{student_id}", response_model=StudentDetail)
async def get_student(
    student_id: uuid.UUID,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> StudentDetail:
    user = await crud.get_student_detail(db, student_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Manually construct StudentDetail to populate course_title and course_slug
    from app.schemas.admin.students import EnrollmentSummary, ExamAttemptSummary, TopicProgressSummary

    enrollments_data = [
        EnrollmentSummary(
            id=e.id,
            course_id=e.course_id,
            started_at=e.started_at,
            completed_at=e.completed_at,
            progress_cached=e.progress_cached,
            course_title=getattr(e.course, "title", None) if e.course else None,
            course_slug=getattr(e.course, "slug", None) if e.course else None,
        )
        for e in user.enrollments
    ]

    topic_progress_data = [
        TopicProgressSummary.model_validate(tp)
        for tp in user.topic_progress
    ]

    exam_attempts_data = [
        ExamAttemptSummary.model_validate(ea)
        for ea in user.exam_attempts
    ]

    return StudentDetail(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        enrollments=enrollments_data,
        topic_progress=topic_progress_data,
        exam_attempts=exam_attempts_data,
    )
