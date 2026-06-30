"""Admin course CRUD router.

Registration line for routers/__init__.py:
    from .admin.courses import router as admin_courses_router
    api_router.include_router(admin_courses_router)
"""

from __future__ import annotations

import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import admin as crud
from app.db import get_db
from app.deps import require_role
from app.models.user import User
from app.schemas.admin.courses import (
    CourseAdminListItem,
    CourseAdminResponse,
    CourseCreate,
    CourseUpdate,
)
from app.services.audit import log_admin_action

router = APIRouter(prefix="/api/v1/admin/courses", tags=["admin-courses"])

_guard = require_role("admin", "instructor")


@router.get("", response_model=list[CourseAdminListItem])
async def list_courses(
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[CourseAdminListItem]:
    courses = await crud.list_courses_admin(db, current_user.role, current_user.id)
    return [CourseAdminListItem.model_validate(c) for c in courses]


@router.post("", response_model=CourseAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    body: CourseCreate,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> CourseAdminResponse:
    data = body.model_dump()
    # Instructors can only own their own courses
    if current_user.role == "instructor" or data.get("instructor_id") is None:
        data["instructor_id"] = current_user.id

    course = await crud.create_course(db, data)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="create",
        entity="course",
        entity_id=course.id,
        payload={"title": course.title, "slug": course.slug, "status": course.status},
    )
    await db.commit()
    # Re-fetch with modules loaded to avoid lazy-load in Pydantic
    refreshed = await crud.get_course_admin(db, course.id)
    return CourseAdminResponse.model_validate(refreshed)


@router.get("/{course_id}", response_model=CourseAdminResponse)
async def get_course(
    course_id: uuid.UUID,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> CourseAdminResponse:
    course = await crud.get_course_admin(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    _assert_owner_or_admin(current_user, course.instructor_id)
    return CourseAdminResponse.model_validate(course)


@router.patch("/{course_id}", response_model=CourseAdminResponse)
async def patch_course(
    course_id: uuid.UUID,
    body: CourseUpdate,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> CourseAdminResponse:
    course = await crud.get_course_admin(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    _assert_owner_or_admin(current_user, course.instructor_id)

    updates = body.model_dump(exclude_none=True)
    # Instructors cannot reassign instructor_id to another user
    if current_user.role == "instructor":
        updates.pop("instructor_id", None)

    updated = await crud.update_course(db, course, updates)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="update",
        entity="course",
        entity_id=course_id,
        payload=updates,
    )
    await db.commit()
    refreshed = await crud.get_course_admin(db, updated.id)
    return CourseAdminResponse.model_validate(refreshed)


@router.post("/{course_id}/publish", response_model=CourseAdminResponse)
async def publish_course(
    course_id: uuid.UUID,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> CourseAdminResponse:
    course = await crud.get_course_admin(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    _assert_owner_or_admin(current_user, course.instructor_id)

    updated = await crud.update_course(db, course, {"status": "publicado"})
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="publish",
        entity="course",
        entity_id=course_id,
        payload={"status": "publicado"},
    )
    await db.commit()
    refreshed = await crud.get_course_admin(db, updated.id)
    return CourseAdminResponse.model_validate(refreshed)


@router.post("/{course_id}/archive", response_model=CourseAdminResponse)
async def archive_course(
    course_id: uuid.UUID,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> CourseAdminResponse:
    course = await crud.get_course_admin(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    _assert_owner_or_admin(current_user, course.instructor_id)

    updated = await crud.update_course(db, course, {"status": "archivado", "archived_at": datetime.now(UTC)})
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="archive",
        entity="course",
        entity_id=course_id,
        payload={"status": "archivado"},
    )
    await db.commit()
    refreshed = await crud.get_course_admin(db, updated.id)
    return CourseAdminResponse.model_validate(refreshed)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: uuid.UUID,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    course = await crud.get_course_admin(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    _assert_owner_or_admin(current_user, course.instructor_id)

    if await crud.course_has_enrollments(db, course_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "has_enrollments",
                "message": "Cannot delete a course with enrolled students. Archive it instead.",
            },
        )

    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="delete",
        entity="course",
        entity_id=course_id,
        payload={"title": course.title},
    )
    await db.delete(course)
    await db.commit()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _assert_owner_or_admin(user: User, instructor_id: uuid.UUID | None) -> None:
    if user.role == "admin":
        return
    if instructor_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own courses",
        )
