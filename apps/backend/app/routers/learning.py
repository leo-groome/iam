from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.crud.exam import (
    get_questions_for_module,
    get_questions_for_topic,
    save_attempt,
)
from app.crud.topic import get_or_create_progress, get_topic_with_module
from app.db import get_db
from app.deps import get_current_user
from app.models.course import Course, Module, Topic
from app.models.progress import Enrollment, ExamAttempt, TopicProgress
from app.models.question import Question
from app.models.user import User
from app.schemas.exam import (
    ExamResponse,
    ExamResult,
    ExamSubmitRequest,
    OptionOut,
    QuestionOut,
)
from app.schemas.topic import (
    HeartbeatRequest,
    HeartbeatResponse,
    MarkContentDoneResponse,
    TopicProgressDetail,
    TopicView,
)
from app.services.progress_engine import (
    check_user_status,
    compute_topic_state,
    on_module_exam_passed,
    on_topic_exam_failed,
    on_topic_exam_passed,
)

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["learning"])

_UNLOCKED_STATES = {"disponible", "contenido_visto", "aprobado", "en_repaso"}
_EXAM_ALLOWED_STATES = {"contenido_visto", "aprobado", "en_repaso"}
_EXAM_TOKEN_TTL_SECONDS = 15 * 60
_VIDEO_COMPLETE_PCT = 95
_MIN_VIDEO_COMPLETE_SECONDS = 5


def _issue_exam_token(
    user_id: uuid.UUID,
    scope: str,
    scope_id: uuid.UUID,
    question_ids: list[uuid.UUID],
) -> str:
    now = int(datetime.now(UTC).timestamp())
    payload = {
        "sub": str(user_id),
        "aud": "exam",
        "scope": scope,
        f"{scope}_id": str(scope_id),
        "question_ids": [str(question_id) for question_id in question_ids],
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + _EXAM_TOKEN_TTL_SECONDS,
    }
    return jwt.encode(payload, settings.media_jwt_secret, algorithm="HS256")


def _validate_exam_token(
    token: str,
    user_id: uuid.UUID,
    scope: str,
    scope_id: uuid.UUID,
) -> tuple[set[str], str]:
    try:
        payload = jwt.decode(
            token,
            settings.media_jwt_secret,
            algorithms=["HS256"],
            audience="exam",
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "exam_token_expired"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "invalid_exam_token"},
        ) from exc

    question_ids = payload.get("question_ids")
    jti = payload.get("jti")
    if (
        payload.get("sub") != str(user_id)
        or payload.get("scope") != scope
        or payload.get(f"{scope}_id") != str(scope_id)
        or not isinstance(question_ids, list)
        or not all(isinstance(question_id, str) for question_id in question_ids)
        or not isinstance(jti, str)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "invalid_exam_token"},
        )
    return set(question_ids), jti


async def _ensure_exam_token_unused(
    db: AsyncSession,
    user_id: uuid.UUID,
    jti: str,
    topic_id: uuid.UUID | None = None,
    module_id: uuid.UUID | None = None,
) -> None:
    stmt = select(ExamAttempt).where(ExamAttempt.user_id == user_id)
    if topic_id is not None:
        stmt = stmt.where(ExamAttempt.topic_id == topic_id)
    if module_id is not None:
        stmt = stmt.where(ExamAttempt.module_id == module_id)

    result = await db.execute(stmt)
    for attempt in result.scalars():
        if isinstance(attempt.answers, dict) and attempt.answers.get("_exam_jti") == jti:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "exam_token_replayed"},
            )


def _grade_signed_answers(
    questions: list[Question],
    body: ExamSubmitRequest,
    signed_question_ids: set[str],
) -> tuple[int, int, dict[str, str]]:
    if not signed_question_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "invalid_exam_token"},
        )

    question_map = {
        str(question.id): question
        for question in questions
        if str(question.id) in signed_question_ids
    }
    if set(question_map) != signed_question_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "invalid_exam_token"},
        )

    answers_payload: dict[str, str] = {}
    correct = 0
    for answer in body.answers:
        question_id = str(answer.question_id)
        option_id = str(answer.option_id)

        if question_id in answers_payload:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "duplicate_answer"},
            )
        if question_id not in signed_question_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "unsigned_question"},
            )

        option_map = {str(option.id): option for option in question_map[question_id].options}
        option = option_map.get(option_id)
        if option is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "invalid_option"},
            )

        answers_payload[question_id] = option_id
        if option.is_correct:
            correct += 1

    return correct, len(signed_question_ids), answers_payload


def _video_pct_from_position(pos_seconds: int, duration_seconds: int | None) -> int:
    if duration_seconds is None or duration_seconds <= 0:
        return 0
    return min(100, max(0, round((pos_seconds / duration_seconds) * 100)))


def _complete_content(tp: TopicProgress) -> None:
    tp.content_completed_at = datetime.now(UTC)  # type: ignore[assignment]
    if tp.state not in ("contenido_visto", "aprobado", "en_repaso"):
        tp.state = "contenido_visto"


async def _require_enrollment(
    db: AsyncSession, user: User, course_id: uuid.UUID
) -> Enrollment:
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course_id,
        )
    )
    enrollment = result.scalar_one_or_none()
    with open('/tmp/backend_debug.log', 'a') as f:
        f.write(
            "DEBUG: _require_enrollment - "
            f"user.id: {user.id}, user.email: {user.email}, "
            f"course_id: {course_id}, enrollment found: {enrollment is not None}\n"
        )
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this course"
        )
    return enrollment


async def _get_topic_or_404(db: AsyncSession, topic_id: uuid.UUID) -> Topic:
    topic = await get_topic_with_module(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return topic


@router.get("/topics/{topic_id}", response_model=TopicView)
async def get_topic(
    topic_id: uuid.UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> TopicView:
    topic = await _get_topic_or_404(db, topic_id)
    await _require_enrollment(db, current_user, topic.module.course_id)

    state = await compute_topic_state(db, current_user, topic)
    tp = await get_or_create_progress(db, current_user, topic)

    if state == "bloqueado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "topic_locked"},
        )

    # Use persisted state if not bloqueado
    real_state = tp.state if tp.state != "bloqueado" else state

    return TopicView(
        id=topic.id,
        title=topic.title,
        content_type=topic.content_type,
        content_body=topic.content_body,
        duration_seconds=topic.duration_seconds,
        has_exam=topic.has_exam,
        exam_min_score=topic.exam_min_score,
        media_key=topic.media_key,
        state=real_state,
        progress=TopicProgressDetail(
            video_last_pos_seconds=tp.video_last_pos_seconds,
            video_max_seen_pct=tp.video_max_seen_pct,
            pdf_last_page=tp.pdf_last_page,
            pdf_total_pages=tp.pdf_total_pages,
        ),
    )


@router.post("/topics/{topic_id}/heartbeat", response_model=HeartbeatResponse)
async def topic_heartbeat(
    topic_id: uuid.UUID,
    body: HeartbeatRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> HeartbeatResponse:
    topic = await _get_topic_or_404(db, topic_id)
    await _require_enrollment(db, current_user, topic.module.course_id)

    state = await compute_topic_state(db, current_user, topic)
    if state == "bloqueado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "topic_locked"},
        )

    tp = await get_or_create_progress(db, current_user, topic)

    if body.type == "video":
        if body.max_seen_pct is not None and body.pos_seconds is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "missing_video_position"},
            )
        if body.pos_seconds is not None:
            tp.video_last_pos_seconds = body.pos_seconds
            duration_seconds = body.duration_seconds or topic.duration_seconds
            server_pct = _video_pct_from_position(body.pos_seconds, duration_seconds)
            tp.video_max_seen_pct = max(tp.video_max_seen_pct, server_pct)
            if (
                body.max_seen_pct is not None
                and body.max_seen_pct >= _VIDEO_COMPLETE_PCT
                and body.pos_seconds >= _MIN_VIDEO_COMPLETE_SECONDS
            ):
                tp.video_max_seen_pct = max(tp.video_max_seen_pct, body.max_seen_pct)
        if tp.video_max_seen_pct >= _VIDEO_COMPLETE_PCT:
            _complete_content(tp)
    elif body.type in ("pdf",):
        if body.last_page is not None:
            tp.pdf_last_page = max(tp.pdf_last_page, body.last_page)
        if body.total_pages is not None:
            tp.pdf_total_pages = body.total_pages
    elif body.type == "texto":
        if body.max_seen_pct is not None:
            tp.video_max_seen_pct = max(tp.video_max_seen_pct, body.max_seen_pct)

    await db.commit()
    await db.refresh(tp)

    real_state = tp.state if tp.state != "bloqueado" else state

    return HeartbeatResponse(
        state=real_state,
        video_last_pos_seconds=tp.video_last_pos_seconds,
        video_max_seen_pct=tp.video_max_seen_pct,
        pdf_last_page=tp.pdf_last_page,
        pdf_total_pages=tp.pdf_total_pages,
    )


@router.post("/topics/{topic_id}/mark-content-done", response_model=MarkContentDoneResponse)
async def mark_content_done(
    topic_id: uuid.UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> MarkContentDoneResponse:
    topic = await _get_topic_or_404(db, topic_id)
    await _require_enrollment(db, current_user, topic.module.course_id)

    tp = await get_or_create_progress(db, current_user, topic)

    if tp.state == "bloqueado":
        state = await compute_topic_state(db, current_user, topic)
        if state == "bloqueado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "topic_locked"},
            )

    ct = topic.content_type

    if ct == "video":
        if tp.video_max_seen_pct < 95:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "content_incomplete"},
            )
    elif ct == "pdf":
        if tp.pdf_total_pages is None or tp.pdf_last_page < tp.pdf_total_pages:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "content_incomplete"},
            )
    elif ct == "imagen":
        # Validate at least 5 seconds since first heartbeat (use content_completed_at as proxy
        # for first interaction timestamp — we use updated_at instead)
        # Server trusts client but checks that topic_progress row is not brand-new (updated_at > created_at + 5s)
        now = datetime.now(UTC)
        created: datetime | None = tp.created_at  # type: ignore[assignment]
        if created is not None:
            # created_at is timezone-aware from DB, compare safely
            elapsed = (now - created).total_seconds() if hasattr(created, "tzinfo") and created.tzinfo else 0
            if elapsed < 5:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"code": "content_incomplete"},
                )
    elif ct == "texto" and tp.video_max_seen_pct < 90:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "content_incomplete"},
        )

    _complete_content(tp)

    await db.commit()
    await db.refresh(tp)

    # Recompute course progress since non-exam topics don't trigger exam_passed
    course_result = await db.execute(
        select(Course).where(Course.id == topic.module.course_id)
    )
    course = course_result.scalar_one_or_none()
    if course is not None:
        from app.services.progress_engine import recompute_course_progress
        pct = await recompute_course_progress(db, current_user, course)
        if pct == 100:
            current_user.status = "completado"
        await db.commit()

    completed_at_raw: datetime | None = tp.content_completed_at  # type: ignore[assignment]
    return MarkContentDoneResponse(
        state=tp.state,
        content_completed_at=completed_at_raw.isoformat() if completed_at_raw else None,
    )


@router.get("/topics/{topic_id}/exam", response_model=ExamResponse)
async def get_topic_exam(
    topic_id: uuid.UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ExamResponse:
    topic = await _get_topic_or_404(db, topic_id)
    await _require_enrollment(db, current_user, topic.module.course_id)

    tp = await get_or_create_progress(db, current_user, topic)
    real_state = tp.state

    if real_state not in _EXAM_ALLOWED_STATES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "topic_locked"},
        )

    # R-EX-08: in en_repaso, exam is blocked until re-completion
    if real_state == "en_repaso" and tp.content_completed_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "repaso_required"},
        )

    questions = await get_questions_for_topic(db, topic_id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No exam questions for this topic"
        )

    random.shuffle(questions)
    question_out = []
    for q in questions:
        options = list(q.options)
        random.shuffle(options)
        question_out.append(
            QuestionOut(
                id=q.id,
                enunciado=q.enunciado,
                options=[OptionOut(id=o.id, texto=o.texto) for o in options],
            )
        )

    exam_token = _issue_exam_token(
        current_user.id,
        "topic",
        topic_id,
        [question.id for question in questions],
    )

    return ExamResponse(
        exam_token=exam_token,
        questions=question_out,
        min_score=topic.exam_min_score,
    )


@router.post("/topics/{topic_id}/exam/submit", response_model=ExamResult)
@limiter.limit("10/minute")
async def submit_topic_exam(
    request: Request,
    topic_id: uuid.UUID,
    body: ExamSubmitRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ExamResult:
    topic = await _get_topic_or_404(db, topic_id)
    await _require_enrollment(db, current_user, topic.module.course_id)

    tp = await get_or_create_progress(db, current_user, topic)

    if tp.state not in _EXAM_ALLOWED_STATES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "topic_locked"},
        )

    questions = await get_questions_for_topic(db, topic_id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No exam questions"
        )

    signed_question_ids, jti = _validate_exam_token(
        body.exam_token,
        current_user.id,
        "topic",
        topic_id,
    )
    await _ensure_exam_token_unused(db, current_user.id, jti, topic_id=topic_id)
    correct, total_questions, answers_payload = _grade_signed_answers(
        questions,
        body,
        signed_question_ids,
    )

    score = int((correct / total_questions) * 100)
    min_score = topic.exam_min_score
    passed = score >= min_score

    answers_payload["_exam_jti"] = jti
    await save_attempt(
        db,
        user_id=current_user.id,
        topic_id=topic_id,
        module_id=None,
        score=score,
        passed=passed,
        min_score_snapshot=min_score,
        answers=answers_payload,
    )

    if passed:
        await on_topic_exam_passed(db, current_user, topic, tp)
        message = "Aprobado. ¡Excelente trabajo!"
    else:
        await on_topic_exam_failed(db, current_user, topic, tp)
        await check_user_status(db, current_user, topic_id)
        message = "No aprobado. Revisa el contenido e intenta de nuevo."

    await db.commit()

    return ExamResult(score=score, passed=passed, min_score=min_score, message=message)


@router.get("/modules/{module_id}/exam", response_model=ExamResponse)
async def get_module_exam(
    module_id: uuid.UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ExamResponse:
    module_result = await db.execute(
        select(Module)
        .where(Module.id == module_id)
        .options(selectinload(Module.topics))
    )
    module = module_result.scalar_one_or_none()
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    await _require_enrollment(db, current_user, module.course_id)

    active_topics = [t for t in module.topics if t.archived_at is None]
    for t in active_topics:
        tp_result = await db.execute(
            select(TopicProgress).where(
                TopicProgress.user_id == current_user.id,
                TopicProgress.topic_id == t.id,
            )
        )
        tp = tp_result.scalar_one_or_none()
        if tp is None or tp.state != "aprobado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "module_topics_incomplete"},
            )

    questions = await get_questions_for_module(db, module_id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No module exam questions"
        )

    random.shuffle(questions)
    question_out = []
    for q in questions:
        options = list(q.options)
        random.shuffle(options)
        question_out.append(
            QuestionOut(
                id=q.id,
                enunciado=q.enunciado,
                options=[OptionOut(id=o.id, texto=o.texto) for o in options],
            )
        )

    exam_token = _issue_exam_token(
        current_user.id,
        "module",
        module_id,
        [question.id for question in questions],
    )

    return ExamResponse(
        exam_token=exam_token,
        questions=question_out,
        min_score=70,
    )


@router.post("/modules/{module_id}/exam/submit", response_model=ExamResult)
@limiter.limit("10/minute")
async def submit_module_exam(
    request: Request,
    module_id: uuid.UUID,
    body: ExamSubmitRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ExamResult:
    module_result = await db.execute(
        select(Module)
        .where(Module.id == module_id)
        .options(selectinload(Module.topics))
    )
    module = module_result.scalar_one_or_none()
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    await _require_enrollment(db, current_user, module.course_id)

    active_topics = [t for t in module.topics if t.archived_at is None]
    for t in active_topics:
        tp_result = await db.execute(
            select(TopicProgress).where(
                TopicProgress.user_id == current_user.id,
                TopicProgress.topic_id == t.id,
            )
        )
        tp = tp_result.scalar_one_or_none()
        if tp is None or tp.state != "aprobado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "module_topics_incomplete"},
            )

    questions = await get_questions_for_module(db, module_id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No module exam questions"
        )

    signed_question_ids, jti = _validate_exam_token(
        body.exam_token,
        current_user.id,
        "module",
        module_id,
    )
    await _ensure_exam_token_unused(db, current_user.id, jti, module_id=module_id)
    correct, total_questions, answers_payload = _grade_signed_answers(
        questions,
        body,
        signed_question_ids,
    )

    score = int((correct / total_questions) * 100)
    min_score = 70
    passed = score >= min_score

    answers_payload["_exam_jti"] = jti
    await save_attempt(
        db,
        user_id=current_user.id,
        topic_id=None,
        module_id=module_id,
        score=score,
        passed=passed,
        min_score_snapshot=min_score,
        answers=answers_payload,
    )

    if passed:
        await on_module_exam_passed(db, current_user, module)
        message = "Módulo completado. ¡Excelente!"
    else:
        message = "No aprobado. Revisa el contenido del módulo."

    await db.commit()

    return ExamResult(score=score, passed=passed, min_score=min_score, message=message)
