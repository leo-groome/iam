from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.exam import count_consecutive_failures
from app.crud.topic import get_or_create_progress
from app.models.course import ContentBlock, Course, Module, Topic
from app.models.progress import ContentBlockProgress, Enrollment, ExamAttempt, TopicProgress
from app.models.user import User

_ATORADO_THRESHOLD = 3

# Only 'video' content blocks gate topic completion. A video block is considered
# watched once the reported max-seen percentage crosses this threshold AND the
# player has reported at least this many seconds of playback (prevents trivial
# skip-to-end claims on very short clips reporting 100% instantly).
_VIDEO_COMPLETE_PCT = 95
_MIN_VIDEO_COMPLETE_SECONDS = 5


def _complete_content(tp: TopicProgress) -> None:
    tp.content_completed_at = datetime.now(UTC)  # type: ignore[assignment]
    if tp.state != "aprobado":
        tp.state = "contenido_visto"


async def _get_topic_progress(
    db: AsyncSession, user_id: uuid.UUID, topic_id: uuid.UUID
) -> TopicProgress | None:
    result = await db.execute(
        select(TopicProgress).where(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id == topic_id,
        )
    )
    return result.scalar_one_or_none()


async def _module_exam_passed(
    db: AsyncSession, user_id: uuid.UUID, module_id: uuid.UUID
) -> bool:
    result = await db.execute(
        select(ExamAttempt).where(
            ExamAttempt.user_id == user_id,
            ExamAttempt.module_id == module_id,
            ExamAttempt.passed.is_(True),
        )
    )
    return result.scalar_one_or_none() is not None


async def _module_has_exam_questions(db: AsyncSession, module_id: uuid.UUID) -> bool:
    from app.models.question import Question

    result = await db.execute(
        select(Question).where(
            Question.module_id == module_id,
            Question.archived_at.is_(None),
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _all_topics_approved(
    db: AsyncSession, user_id: uuid.UUID, topics: list[Topic]
) -> bool:
    active_topics = [t for t in topics if t.archived_at is None]
    for t in active_topics:
        tp = await _get_topic_progress(db, user_id, t.id)
        if tp is None or tp.state != "aprobado":
            return False
    return True


async def _prev_module_complete(
    db: AsyncSession, user_id: uuid.UUID, prev_module: Module
) -> bool:
    active_topics = [t for t in prev_module.topics if t.archived_at is None]
    all_approved = await _all_topics_approved(db, user_id, active_topics)
    if not all_approved:
        return False
    has_questions = await _module_has_exam_questions(db, prev_module.id)
    if has_questions:
        return await _module_exam_passed(db, user_id, prev_module.id)
    return True


async def compute_topic_state(db: AsyncSession, user: User, topic: Topic) -> str:
    tp = await _get_topic_progress(db, user.id, topic.id)
    if tp is not None and tp.state != "bloqueado":
        return tp.state

    # Always re-fetch topic with eager-loaded module+topics to avoid lazy load in async context
    topic_result = await db.execute(
        select(Topic)
        .where(Topic.id == topic.id)
        .options(selectinload(Topic.module).selectinload(Module.topics))
    )
    fresh_topic = topic_result.scalar_one_or_none()
    if fresh_topic is None:
        return "bloqueado"

    module: Module = fresh_topic.module
    sorted_topics = sorted(
        [t for t in module.topics if t.archived_at is None],
        key=lambda t: t.order_index,
    )

    if not sorted_topics:
        return "bloqueado"

    topic_idx = next(
        (i for i, t in enumerate(sorted_topics) if t.id == topic.id), None
    )
    if topic_idx is None:
        return "bloqueado"

    if topic_idx > 0:
        prev_topic = sorted_topics[topic_idx - 1]
        prev_tp = await _get_topic_progress(db, user.id, prev_topic.id)
        if prev_tp is None or prev_tp.state != "aprobado":
            return "bloqueado"
        return "disponible"

    # First topic of this module — check previous module
    course_result = await db.execute(
        select(Course)
        .where(Course.id == module.course_id)
        .options(selectinload(Course.modules).selectinload(Module.topics))
    )
    course = course_result.scalar_one_or_none()
    if course is None:
        return "bloqueado"

    active_modules = sorted(
        [m for m in course.modules if m.archived_at is None],
        key=lambda m: m.order_index,
    )

    module_idx = next(
        (i for i, m in enumerate(active_modules) if m.id == module.id), None
    )
    if module_idx is None:
        return "bloqueado"

    if module_idx == 0:
        return "disponible"

    prev_module = active_modules[module_idx - 1]
    # Need topics loaded on prev_module
    prev_module_result = await db.execute(
        select(Module)
        .where(Module.id == prev_module.id)
        .options(selectinload(Module.topics))
    )
    prev_module_loaded = prev_module_result.scalar_one_or_none()
    if prev_module_loaded is None:
        return "bloqueado"

    complete = await _prev_module_complete(db, user.id, prev_module_loaded)
    return "disponible" if complete else "bloqueado"


async def recompute_course_progress(
    db: AsyncSession, user: User, course: Course
) -> int:
    modules_result = await db.execute(
        select(Module)
        .where(Module.course_id == course.id, Module.archived_at.is_(None))
        .options(selectinload(Module.topics))
    )
    modules = list(modules_result.scalars().all())

    total = 0
    approved = 0
    for m in modules:
        for t in m.topics:
            if t.archived_at is not None:
                continue
            total += 1
            tp = await _get_topic_progress(db, user.id, t.id)
            if tp is not None:
                if t.has_exam and tp.state == "aprobado":
                    approved += 1
                elif not t.has_exam and tp.state in ("contenido_visto", "aprobado", "en_repaso"):
                    approved += 1

    pct = int((approved / total) * 100) if total > 0 else 0

    enrollment_result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course.id,
        )
    )
    enrollment = enrollment_result.scalar_one_or_none()
    if enrollment is not None:
        enrollment.progress_cached = pct
        if pct == 100 and enrollment.completed_at is None:
            enrollment.completed_at = datetime.now(UTC)  # type: ignore[assignment]

    return pct


async def on_topic_exam_passed(
    db: AsyncSession, user: User, topic: Topic, tp: TopicProgress
) -> None:
    tp.state = "aprobado"
    course_result = await db.execute(
        select(Course).where(Course.id == topic.module.course_id)
    )
    course = course_result.scalar_one_or_none()
    if course is not None:
        pct = await recompute_course_progress(db, user, course)
        if pct == 100:
            user.status = "completado"


def _block_progress_complete(block: ContentBlock, bp: ContentBlockProgress | None) -> bool:
    if bp is None:
        return False
    if block.kind == "video":
        return (
            bp.video_max_seen_pct >= _VIDEO_COMPLETE_PCT
            and bp.video_last_pos_seconds >= _MIN_VIDEO_COMPLETE_SECONDS
        )
    if block.kind == "pdf":
        return (
            bp.pdf_total_pages is not None
            and bp.pdf_total_pages > 0
            and bp.pdf_last_page >= bp.pdf_total_pages
        )
    return False


async def recompute_content_completion(
    db: AsyncSession, user: User, topic: Topic
) -> bool:
    """Recompute and (if reached) persist content-completion for a topic's blocks.

    Only 'video' and 'pdf' blocks gate completion (required_blocks). If the topic
    has at least one required block, it is complete iff EVERY required block has a
    ContentBlockProgress row for this user satisfying its kind's threshold:
      - video: video_max_seen_pct >= _VIDEO_COMPLETE_PCT AND
        video_last_pos_seconds >= _MIN_VIDEO_COMPLETE_SECONDS.
      - pdf: pdf_total_pages is set and > 0, AND pdf_last_page >= pdf_total_pages
        (the frontend reports the real page count from pdf.js).
    If the topic has no required blocks (only audio/imagen/texto), this returns
    False — completion for those topics is left to the honor-system
    mark-content-done flow.

    Returns whether the topic's required content is complete. As a side effect,
    when complete, marks the TopicProgress as content-completed (flushed, not
    committed — caller commits).
    """
    result = await db.execute(
        select(Topic).where(Topic.id == topic.id).options(selectinload(Topic.blocks))
    )
    fresh_topic = result.scalar_one_or_none()
    if fresh_topic is None:
        return False

    required_blocks = [b for b in fresh_topic.blocks if b.kind in ("video", "pdf")]
    if not required_blocks:
        return False

    block_ids = [b.id for b in required_blocks]
    bp_result = await db.execute(
        select(ContentBlockProgress).where(
            ContentBlockProgress.user_id == user.id,
            ContentBlockProgress.block_id.in_(block_ids),
        )
    )
    progress_by_block = {bp.block_id: bp for bp in bp_result.scalars()}

    complete = all(
        _block_progress_complete(block, progress_by_block.get(block.id))
        for block in required_blocks
    )

    if complete:
        tp = await get_or_create_progress(db, user, fresh_topic)
        _complete_content(tp)

    return complete


async def on_topic_exam_failed(
    db: AsyncSession, user: User, topic: Topic, tp: TopicProgress
) -> None:
    tp.state = "en_repaso"
    tp.video_max_seen_pct = 0
    tp.pdf_last_page = 0
    tp.content_completed_at = None

    # Force re-watch of video blocks AND re-read of pdf blocks in repaso: reset
    # per-block progress too, so a failed exam re-gates on both required kinds.
    gating_blocks_result = await db.execute(
        select(ContentBlock).where(
            ContentBlock.topic_id == topic.id,
            ContentBlock.kind.in_(("video", "pdf")),
        )
    )
    blocks_by_id = {b.id: b for b in gating_blocks_result.scalars()}
    if blocks_by_id:
        block_progress_result = await db.execute(
            select(ContentBlockProgress).where(
                ContentBlockProgress.user_id == user.id,
                ContentBlockProgress.block_id.in_(blocks_by_id.keys()),
            )
        )
        for bp in block_progress_result.scalars():
            block = blocks_by_id[bp.block_id]
            if block.kind == "video":
                bp.video_max_seen_pct = 0
                bp.video_last_pos_seconds = 0
            elif block.kind == "pdf":
                bp.pdf_last_page = 0
                bp.pdf_total_pages = None
            bp.completed_at = None


async def on_module_exam_passed(
    db: AsyncSession, user: User, module: Module
) -> None:
    pass


async def check_user_status(
    db: AsyncSession, user: User, topic_id: uuid.UUID
) -> None:
    consecutive = await count_consecutive_failures(db, user.id, topic_id)
    if consecutive >= _ATORADO_THRESHOLD:
        user.status = "atorado"
