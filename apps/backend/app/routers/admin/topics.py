"""Admin topics router.

Registration line for routers/__init__.py:
    from .admin.topics import router as admin_topics_router
    api_router.include_router(admin_topics_router)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import admin as crud
from app.db import get_db
from app.deps import require_role
from app.models.user import User
from app.routers.admin.permissions import assert_can_manage_module, assert_can_manage_topic
from app.schemas.admin.topics import TopicCreate, TopicReorderBody, TopicResponse, TopicUpdate
from app.services.audit import log_admin_action

router = APIRouter(tags=["admin-topics"])

_guard = require_role("admin", "instructor")


@router.post(
    "/api/v1/admin/modules/{module_id}/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_topic(
    module_id: uuid.UUID,
    body: TopicCreate,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> TopicResponse:
    await assert_can_manage_module(db, current_user, module_id)

    order_index = body.order_index
    if order_index is None:
        order_index = await crud.next_topic_order(db, module_id)

    data: dict[str, object] = {
        "module_id": module_id,
        "title": body.title,
        "content_type": body.content_type,
        "content_body": body.content_body,
        "media_key": body.media_key,
        "duration_seconds": body.duration_seconds,
        "has_exam": body.has_exam,
        "exam_min_score": body.exam_min_score,
        "order_index": order_index,
    }
    topic = await crud.create_topic(db, data)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="create",
        entity="topic",
        entity_id=topic.id,
        payload={"module_id": str(module_id), "title": topic.title},
    )
    await db.commit()
    await db.refresh(topic)
    return TopicResponse.model_validate(topic)


@router.patch("/api/v1/admin/topics/{topic_id}", response_model=TopicResponse)
async def patch_topic(
    topic_id: uuid.UUID,
    body: TopicUpdate,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> TopicResponse:
    topic = await crud.get_topic(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    await assert_can_manage_topic(db, current_user, topic_id)

    updates = body.model_dump(exclude_none=True)
    # R-ADM-05: min_score change only affects future attempts (snapshot is stored at attempt time)
    # No special logic needed here — the snapshot happens in exam_engine.py at attempt creation.
    updated = await crud.update_topic(db, topic, updates)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="update",
        entity="topic",
        entity_id=topic_id,
        payload=updates,
    )
    await db.commit()
    await db.refresh(updated)
    return TopicResponse.model_validate(updated)


@router.delete("/api/v1/admin/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: uuid.UUID,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    """R-ADM-03: Topics with student progress cannot be deleted."""
    topic = await crud.get_topic(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    await assert_can_manage_topic(db, current_user, topic_id)

    if await crud.topic_has_progress(db, topic_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "has_progress",
                "message": "Cannot delete a topic with student progress. Edit content instead.",
            },
        )

    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="delete",
        entity="topic",
        entity_id=topic_id,
        payload={"title": topic.title},
    )
    await db.delete(topic)
    await db.commit()


@router.post("/api/v1/admin/topics/reorder", response_model=list[TopicResponse])
async def reorder_topics(
    body: TopicReorderBody,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[TopicResponse]:
    await assert_can_manage_module(db, current_user, body.module_id)

    updated = await crud.reorder_topics(db, body.module_id, body.order)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="reorder",
        entity="topic",
        entity_id=body.module_id,
        payload={"order": [str(i) for i in body.order]},
    )
    await db.commit()
    return [TopicResponse.model_validate(t) for t in updated]
