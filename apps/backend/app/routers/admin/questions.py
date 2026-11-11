"""Admin questions router.

Registration line for routers/__init__.py:
    from .admin.questions import router as admin_questions_router
    api_router.include_router(admin_questions_router)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud import admin as crud
from app.db import get_db
from app.deps import require_role
from app.models.question import Question
from app.models.user import User
from app.routers.admin.permissions import (
    assert_can_manage_module,
    assert_can_manage_question,
    assert_can_manage_topic,
)
from app.schemas.admin.questions import (
    QuestionBulkItem,
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
        order_index=await crud.next_question_order(db, topic_id=topic_id, module_id=None),
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
    body: list[QuestionBulkItem],
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[QuestionResponse]:
    """Sincroniza el banco del tema: upsert por `id`, archiva solo las preguntas omitidas."""
    await assert_can_manage_topic(db, current_user, topic_id)
    topic = await crud.get_topic(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    if not body and topic.has_exam:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "questions_required",
                "message": "Un tema con examen necesita al menos 1 pregunta.",
            },
        )

    existing = {q.id: q for q in await crud.list_topic_questions(db, topic_id)}
    kept: set[uuid.UUID] = set()
    ids = [i.id for i in body if i.id is not None]
    if len(ids) != len(set(ids)) or any(i not in existing for i in ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Una pregunta no pertenece a este tema",
        )

    for idx, item in enumerate(body):
        if item.id is None:
            await crud.create_question(
                db,
                enunciado=item.enunciado,
                topic_id=topic_id,
                module_id=None,
                options_data=[o.model_dump() for o in item.options],
                order_index=idx,
            )
            continue
        kept.add(item.id)
        try:
            crud.apply_question_edit(
                existing[item.id], enunciado=item.enunciado, options=item.options, order_index=idx
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    for question_id, question in existing.items():
        if question_id not in kept:
            await crud.archive_question(db, question)
    await db.flush()

    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="replace_bulk",
        entity="topic_questions",
        entity_id=topic_id,
        payload={"topic_id": str(topic_id), "question_count": len(body)},
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
        order_index=await crud.next_question_order(db, topic_id=None, module_id=module_id),
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
    await assert_can_manage_question(db, current_user, question_id)
    result = await db.execute(
        select(Question).where(Question.id == question_id)
        .options(selectinload(Question.options)).with_for_update()
        .execution_options(populate_existing=True)
    )
    question = result.scalar_one_or_none()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    if body.enunciado is None and body.options is None:
        raise HTTPException(status_code=422, detail="Enunciado u opciones requeridos")

    try:
        crud.apply_question_edit(question, enunciado=body.enunciado, options=body.options)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await db.flush()
    updated = question
    await log_admin_action(
        db, actor_id=current_user.id, action="update", entity="question",
        entity_id=question_id,
        payload={"enunciado": question.enunciado[:80], "options_updated": body.options is not None},
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
