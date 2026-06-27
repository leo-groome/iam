"""Admin questions router.

Registration line for routers/__init__.py:
    from .admin.questions import router as admin_questions_router
    api_router.include_router(admin_questions_router)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import admin as crud
from app.db import get_db
from app.deps import require_role
from app.models.user import User
from app.routers.admin.permissions import (
    assert_can_manage_module,
    assert_can_manage_option,
    assert_can_manage_question,
    assert_can_manage_topic,
)
from app.schemas.admin.questions import (
    OptionResponse,
    OptionUpdate,
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
)
from app.services.audit import log_admin_action

router = APIRouter(tags=["admin-questions"])

_guard = require_role("admin", "instructor")


@router.post(
    "/api/v1/admin/topics/{topic_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_question_for_topic(
    topic_id: uuid.UUID,
    body: QuestionCreate,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> QuestionResponse:
    await assert_can_manage_topic(db, current_user, topic_id)

    options_data = [o.model_dump() for o in body.options]
    question = await crud.create_question(
        db,
        enunciado=body.enunciado,
        topic_id=topic_id,
        module_id=None,
        options_data=options_data,
        order_index=body.order_index,
    )
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="create",
        entity="question",
        entity_id=question.id,
        payload={"topic_id": str(topic_id), "enunciado": body.enunciado[:80]},
    )
    await db.commit()
    await db.refresh(question, ["options"])
    return QuestionResponse.model_validate(question)


@router.post(
    "/api/v1/admin/topics/{topic_id}/questions/bulk",
    response_model=list[QuestionResponse],
)
async def replace_questions_for_topic(
    topic_id: uuid.UUID,
    body: list[QuestionCreate],
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[QuestionResponse]:
    await assert_can_manage_topic(db, current_user, topic_id)

    existing = await crud.list_topic_questions(db, topic_id)
    for question in existing:
        await crud.archive_question(db, question)

    created = []
    for idx, question_body in enumerate(body):
        question = await crud.create_question(
            db,
            enunciado=question_body.enunciado,
            topic_id=topic_id,
            module_id=None,
            options_data=[o.model_dump() for o in question_body.options],
            order_index=idx,
        )
        created.append(question)

    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="replace_bulk",
        entity="topic_questions",
        entity_id=topic_id,
        payload={"topic_id": str(topic_id), "question_count": len(created)},
    )
    await db.commit()

    refreshed = await crud.list_topic_questions(db, topic_id)
    return [QuestionResponse.model_validate(q) for q in refreshed]


@router.post(
    "/api/v1/admin/modules/{module_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_question_for_module(
    module_id: uuid.UUID,
    body: QuestionCreate,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> QuestionResponse:
    await assert_can_manage_module(db, current_user, module_id)

    options_data = [o.model_dump() for o in body.options]
    question = await crud.create_question(
        db,
        enunciado=body.enunciado,
        topic_id=None,
        module_id=module_id,
        options_data=options_data,
        order_index=body.order_index,
    )
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="create",
        entity="question",
        entity_id=question.id,
        payload={"module_id": str(module_id), "enunciado": body.enunciado[:80]},
    )
    await db.commit()
    await db.refresh(question, ["options"])
    return QuestionResponse.model_validate(question)


@router.get("/api/v1/admin/questions/{question_id}", response_model=QuestionResponse)
async def get_question_detail(
    question_id: uuid.UUID,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> QuestionResponse:
    await assert_can_manage_question(db, current_user, question_id)
    question = await crud.get_question_with_options(db, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return QuestionResponse.model_validate(question)


@router.get("/api/v1/admin/modules/{module_id}/questions", response_model=list[QuestionResponse])
async def list_module_questions(
    module_id: uuid.UUID,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[QuestionResponse]:
    await assert_can_manage_module(db, current_user, module_id)
    questions = await crud.list_module_questions(db, module_id)
    return [QuestionResponse.model_validate(q) for q in questions]


@router.patch("/api/v1/admin/questions/{question_id}", response_model=QuestionResponse)
async def patch_question(
    question_id: uuid.UUID,
    body: QuestionUpdate,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> QuestionResponse:
    """R-ADM-04: Editing enunciado does not affect historical exam_attempts scores."""
    question = await crud.get_question(db, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    await assert_can_manage_question(db, current_user, question_id)

    if body.enunciado is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="enunciado required")

    updated = await crud.update_question(db, question, body.enunciado)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="update",
        entity="question",
        entity_id=question_id,
        payload={"enunciado": body.enunciado[:80]},
    )
    await db.commit()
    await db.refresh(updated, ["options"])
    return QuestionResponse.model_validate(updated)


@router.delete("/api/v1/admin/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_question(
    question_id: uuid.UUID,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    """R-ADM-04: Soft-delete via archived_at. Historical attempts unaffected."""
    question = await crud.get_question(db, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    await assert_can_manage_question(db, current_user, question_id)

    await crud.archive_question(db, question)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="archive",
        entity="question",
        entity_id=question_id,
        payload={"enunciado": question.enunciado[:80]},
    )
    await db.commit()


@router.patch("/api/v1/admin/options/{option_id}", response_model=OptionResponse)
async def patch_option(
    option_id: uuid.UUID,
    body: OptionUpdate,
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> OptionResponse:
    option = await crud.get_option(db, option_id)
    if option is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Option not found")
    await assert_can_manage_option(db, current_user, option_id)

    updates = body.model_dump(exclude_none=True)
    updated = await crud.update_option(db, option, updates)
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="update",
        entity="option",
        entity_id=option_id,
        payload=updates,
    )
    await db.commit()
    await db.refresh(updated)
    return OptionResponse.model_validate(updated)
