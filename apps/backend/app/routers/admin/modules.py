"""Admin modules router.

Registration line for routers/__init__.py:
    from .admin.modules import router as admin_modules_router
    api_router.include_router(admin_modules_router)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import admin as crud
from app.db import get_db
from app.deps import require_role
from app.models.user import User
from app.routers.admin.permissions import assert_can_manage_course, assert_can_manage_module
from app.schemas.admin.modules import ModuleCreate, ModuleResponse, ModuleUpdate, ReorderBody
from app.services.audit import log_admin_action

router = APIRouter(tags=["admin-modules"])

_guard = require_role("admin", "instructor")


@router.post(
    "/api/v1/admin/courses/{course_id}/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_module(
    course_id: uuid.UUID,
    body: ModuleCreate,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ModuleResponse:
    await assert_can_manage_course(db, current_user, course_id)

    order_index = body.order_index
    if order_index is None:
        order_index = await crud.next_module_order(db, course_id)

    data: dict[str, object] = {
        "course_id": course_id,
        "title": body.title,
        "description": body.description,
        "order_index": order_index,
    }
    mod = await crud.create_module(db, data)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="create",
        entity="module",
        entity_id=mod.id,
        payload={"course_id": str(course_id), "title": mod.title},
    )
    await db.commit()
    await db.refresh(mod)
    return ModuleResponse.model_validate(mod)


@router.patch("/api/v1/admin/modules/{module_id}", response_model=ModuleResponse)
async def patch_module(
    module_id: uuid.UUID,
    body: ModuleUpdate,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ModuleResponse:
    mod = await crud.get_module(db, module_id)
    if mod is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    await assert_can_manage_module(db, current_user, module_id)

    updates = body.model_dump(exclude_none=True)
    updated = await crud.update_module(db, mod, updates)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="update",
        entity="module",
        entity_id=module_id,
        payload=updates,
    )
    await db.commit()
    await db.refresh(updated)
    return ModuleResponse.model_validate(updated)


@router.delete("/api/v1/admin/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: uuid.UUID,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    mod = await crud.get_module(db, module_id)
    if mod is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    await assert_can_manage_module(db, current_user, module_id)

    if await crud.module_has_progress(db, module_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "has_progress",
                "message": "Cannot delete a module with student progress. Archive topics individually.",
            },
        )

    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="delete",
        entity="module",
        entity_id=module_id,
        payload={"title": mod.title},
    )
    await db.delete(mod)
    await db.commit()


@router.post("/api/v1/admin/modules/reorder", response_model=list[ModuleResponse])
async def reorder_modules(
    body: ReorderBody,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[ModuleResponse]:
    await assert_can_manage_course(db, current_user, body.course_id)

    updated = await crud.reorder_modules(db, body.course_id, body.order)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="reorder",
        entity="module",
        entity_id=body.course_id,
        payload={"order": [str(i) for i in body.order]},
    )
    await db.commit()
    return [ModuleResponse.model_validate(m) for m in updated]
