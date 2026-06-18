"""Admin CRUD helpers.

Thin query layer — no business logic. Routers own validation and audit calls.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import Course, Module, Topic
from app.models.progress import Enrollment, ExamAttempt, TopicProgress
from app.models.question import Option, Question
from app.models.user import User

# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------


async def list_courses_admin(
    db: AsyncSession,
    actor_role: str,
    actor_id: uuid.UUID,
) -> list[Course]:
    stmt = select(Course).order_by(Course.order_index, Course.created_at)
    if actor_role == "instructor":
        stmt = stmt.where(Course.instructor_id == actor_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_course_admin(db: AsyncSession, course_id: uuid.UUID) -> Course | None:
    stmt = (
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.modules).selectinload(Module.topics)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_course(db: AsyncSession, data: dict[str, object]) -> Course:
    course = Course(**data)
    db.add(course)
    await db.flush()
    return course


async def update_course(
    db: AsyncSession, course: Course, updates: dict[str, object]
) -> Course:
    for field, value in updates.items():
        setattr(course, field, value)
    await db.flush()
    return course


async def course_has_enrollments(db: AsyncSession, course_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(func.count()).select_from(Enrollment).where(Enrollment.course_id == course_id)
    )
    return (result.scalar() or 0) > 0


# ---------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------


async def get_module(db: AsyncSession, module_id: uuid.UUID) -> Module | None:
    result = await db.execute(select(Module).where(Module.id == module_id))
    return result.scalar_one_or_none()


async def next_module_order(db: AsyncSession, course_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.max(Module.order_index)).where(Module.course_id == course_id)
    )
    max_idx = result.scalar()
    return (max_idx or 0) + 1


async def create_module(db: AsyncSession, data: dict[str, object]) -> Module:
    mod = Module(**data)
    db.add(mod)
    await db.flush()
    return mod


async def update_module(
    db: AsyncSession, mod: Module, updates: dict[str, object]
) -> Module:
    for field, value in updates.items():
        setattr(mod, field, value)
    await db.flush()
    return mod


async def module_has_progress(db: AsyncSession, module_id: uuid.UUID) -> bool:
    """Return True if any topic in this module has TopicProgress rows."""
    topic_ids_q = select(Topic.id).where(Topic.module_id == module_id)
    result = await db.execute(
        select(func.count())
        .select_from(TopicProgress)
        .where(TopicProgress.topic_id.in_(topic_ids_q))
    )
    return (result.scalar() or 0) > 0


async def reorder_modules(
    db: AsyncSession, course_id: uuid.UUID, ordered_ids: list[uuid.UUID]
) -> list[Module]:
    result = await db.execute(
        select(Module).where(Module.course_id == course_id)
    )
    modules_by_id = {m.id: m for m in result.scalars().all()}
    updated: list[Module] = []
    for idx, mid in enumerate(ordered_ids):
        mod = modules_by_id.get(mid)
        if mod is not None:
            mod.order_index = idx
            updated.append(mod)
    await db.flush()
    return updated


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------


async def get_topic(db: AsyncSession, topic_id: uuid.UUID) -> Topic | None:
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    return result.scalar_one_or_none()


async def next_topic_order(db: AsyncSession, module_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.max(Topic.order_index)).where(Topic.module_id == module_id)
    )
    max_idx = result.scalar()
    return (max_idx or 0) + 1


async def create_topic(db: AsyncSession, data: dict[str, object]) -> Topic:
    topic = Topic(**data)
    db.add(topic)
    await db.flush()
    return topic


async def update_topic(
    db: AsyncSession, topic: Topic, updates: dict[str, object]
) -> Topic:
    for field, value in updates.items():
        setattr(topic, field, value)
    await db.flush()
    return topic


async def topic_has_progress(db: AsyncSession, topic_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(func.count())
        .select_from(TopicProgress)
        .where(TopicProgress.topic_id == topic_id)
    )
    return (result.scalar() or 0) > 0


async def reorder_topics(
    db: AsyncSession, module_id: uuid.UUID, ordered_ids: list[uuid.UUID]
) -> list[Topic]:
    result = await db.execute(
        select(Topic).where(Topic.module_id == module_id)
    )
    topics_by_id = {t.id: t for t in result.scalars().all()}
    updated: list[Topic] = []
    for idx, tid in enumerate(ordered_ids):
        topic = topics_by_id.get(tid)
        if topic is not None:
            topic.order_index = idx
            updated.append(topic)
    await db.flush()
    return updated


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------


async def get_question(
    db: AsyncSession, question_id: uuid.UUID
) -> Question | None:
    stmt = (
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.options))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_question(
    db: AsyncSession,
    enunciado: str,
    topic_id: uuid.UUID | None,
    module_id: uuid.UUID | None,
    options_data: list[dict[str, object]],
) -> Question:
    question = Question(
        enunciado=enunciado,
        topic_id=topic_id,
        module_id=module_id,
    )
    db.add(question)
    await db.flush()
    for idx, opt in enumerate(options_data):
        option = Option(
            question_id=question.id,
            texto=str(opt["texto"]),
            is_correct=bool(opt["is_correct"]),
            order_index=int(opt.get("order_index", idx)),  # type: ignore[call-overload]
        )
        db.add(option)
    await db.flush()
    await db.refresh(question, ["options"])
    return question


async def update_question(
    db: AsyncSession, question: Question, enunciado: str
) -> Question:
    question.enunciado = enunciado
    await db.flush()
    return question


async def archive_question(
    db: AsyncSession, question: Question
) -> Question:
    question.archived_at = datetime.now(UTC)  # type: ignore[assignment]
    await db.flush()
    return question


async def get_option(db: AsyncSession, option_id: uuid.UUID) -> Option | None:
    result = await db.execute(select(Option).where(Option.id == option_id))
    return result.scalar_one_or_none()


async def update_option(
    db: AsyncSession, option: Option, updates: dict[str, object]
) -> Option:
    for field, value in updates.items():
        setattr(option, field, value)
    await db.flush()
    return option


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------

STUCK_CONSECUTIVE_FAILS = 3


def _is_stuck_from_attempts(attempts: list[ExamAttempt]) -> bool:
    """Check if the last N attempts for any single topic are all failures."""
    from collections import defaultdict

    by_topic: dict[uuid.UUID, list[bool]] = defaultdict(list)
    for a in sorted(attempts, key=lambda x: x.created_at):  # type: ignore[arg-type, return-value]
        if a.topic_id is not None:
            by_topic[a.topic_id].append(a.passed)

    for passed_list in by_topic.values():
        tail = passed_list[-STUCK_CONSECUTIVE_FAILS:]
        if len(tail) >= STUCK_CONSECUTIVE_FAILS and not any(tail):
            return True
    return False


async def list_students(
    db: AsyncSession,
    q: str | None,
    status: str | None,
    page: int,
    page_size: int,
) -> tuple[list[tuple[User, bool]], int]:
    """Returns (list of (user, is_stuck), total_count)."""
    stmt = select(User).where(User.role == "estudiante")

    if q and len(q) >= 2:
        like = f"%{q}%"
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(User.full_name.ilike(like), User.email.ilike(like))
        )

    if status:
        stmt = stmt.where(User.status == status)

    count_result = await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )
    total = count_result.scalar() or 0

    stmt = stmt.order_by(desc(User.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    users = list(result.scalars().all())

    rows: list[tuple[User, bool]] = []
    for user in users:
        attempts_result = await db.execute(
            select(ExamAttempt).where(ExamAttempt.user_id == user.id)
        )
        attempts = list(attempts_result.scalars().all())
        rows.append((user, _is_stuck_from_attempts(attempts)))

    return rows, total


async def get_student_detail(
    db: AsyncSession, student_id: uuid.UUID
) -> User | None:
    stmt = (
        select(User)
        .where(User.id == student_id, User.role == "estudiante")
        .options(
            selectinload(User.enrollments),
            selectinload(User.topic_progress),
            selectinload(User.exam_attempts),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


async def iter_enrollments_csv(db: AsyncSession) -> AsyncGenerator[str, None]:
    """Yield CSV rows for enrollment export."""
    yield "enrollment_id,user_id,course_id,started_at,completed_at,progress_pct\n"
    result = await db.execute(
        select(Enrollment).order_by(Enrollment.started_at)
    )
    for row in result.scalars():
        yield (
            f"{row.id},{row.user_id},{row.course_id},"
            f"{row.started_at},{row.completed_at or ''},"
            f"{row.progress_cached}\n"
        )


async def iter_completions_csv(db: AsyncSession) -> AsyncGenerator[str, None]:
    """Yield CSV rows for completions export."""
    yield "enrollment_id,user_id,course_id,completed_at\n"
    result = await db.execute(
        select(Enrollment)
        .where(Enrollment.completed_at.is_not(None))
        .order_by(Enrollment.completed_at)
    )
    for row in result.scalars():
        yield f"{row.id},{row.user_id},{row.course_id},{row.completed_at}\n"


async def iter_exam_attempts_csv(db: AsyncSession) -> AsyncGenerator[str, None]:
    """Yield CSV rows for exam attempts export."""
    yield "attempt_id,user_id,topic_id,module_id,score,passed,min_score,created_at\n"
    result = await db.execute(
        select(ExamAttempt).order_by(ExamAttempt.created_at)
    )
    for row in result.scalars():
        yield (
            f"{row.id},{row.user_id},{row.topic_id or ''},"
            f"{row.module_id or ''},{row.score},{row.passed},"
            f"{row.min_score_snapshot},{row.created_at}\n"
        )


async def topic_pass_rate(
    db: AsyncSession, course_id: uuid.UUID
) -> list[dict[str, object]]:
    """Pass rate per topic in a course (active topics only)."""
    topics_result = await db.execute(
        select(Topic)
        .join(Module, Topic.module_id == Module.id)
        .where(Module.course_id == course_id, Topic.archived_at.is_(None))
    )
    topics = list(topics_result.scalars().all())

    rows: list[dict[str, object]] = []
    for topic in topics:
        attempts_result = await db.execute(
            select(ExamAttempt).where(ExamAttempt.topic_id == topic.id)
        )
        attempts = list(attempts_result.scalars().all())
        total = len(attempts)
        passed = sum(1 for a in attempts if a.passed)
        rows.append(
            {
                "topic_id": topic.id,
                "title": topic.title,
                "total_attempts": total,
                "passed_attempts": passed,
                "pass_rate": round(passed / total * 100, 1) if total > 0 else None,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


async def get_dashboard_kpis(db: AsyncSession) -> dict[str, object]:
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)

    total_students = (
        await db.execute(
            select(func.count()).select_from(User).where(User.role == "estudiante")
        )
    ).scalar() or 0

    new_students = (
        await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.role == "estudiante", User.created_at >= week_ago)
        )
    ).scalar() or 0

    active_courses = (
        await db.execute(
            select(func.count()).select_from(Course).where(Course.status == "publicado")
        )
    ).scalar() or 0

    total_enrollments = (
        await db.execute(select(func.count()).select_from(Enrollment))
    ).scalar() or 0

    completed_enrollments = (
        await db.execute(
            select(func.count())
            .select_from(Enrollment)
            .where(Enrollment.completed_at.is_not(None))
        )
    ).scalar() or 0

    completion_rate = (
        round(completed_enrollments / total_enrollments * 100, 1)
        if total_enrollments > 0
        else 0.0
    )

    avg_score_result = (
        await db.execute(select(func.avg(ExamAttempt.score)).select_from(ExamAttempt))
    ).scalar()
    avg_exam_score = round(float(avg_score_result), 1) if avg_score_result is not None else 0.0

    # Stuck students: status == 'atorado'
    stuck_students = (
        await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.role == "estudiante", User.status == "atorado")
        )
    ).scalar() or 0

    # Enrollments per week (last 12 weeks)
    enrollments_per_week: list[dict[str, object]] = []
    for i in range(11, -1, -1):
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)
        count = (
            await db.execute(
                select(func.count())
                .select_from(Enrollment)
                .where(
                    Enrollment.started_at >= week_start,
                    Enrollment.started_at < week_end,
                )
            )
        ).scalar() or 0
        enrollments_per_week.append(
            {"week_start": week_start.date().isoformat(), "count": count}
        )

    # Top 10 completions per course
    comp_result = await db.execute(
        select(Enrollment.course_id, func.count().label("cnt"))
        .where(Enrollment.completed_at.is_not(None))
        .group_by(Enrollment.course_id)
        .order_by(desc("cnt"))
        .limit(10)
    )
    completions_per_course: list[dict[str, object]] = []
    for course_id_val, cnt in comp_result.all():
        course_row = await db.execute(
            select(Course.title).where(Course.id == course_id_val)
        )
        title = course_row.scalar() or ""
        completions_per_course.append(
            {"course_id": course_id_val, "title": title, "completions": cnt}
        )

    return {
        "total_students": total_students,
        "new_students_last_7d": new_students,
        "active_courses": active_courses,
        "completion_rate": completion_rate,
        "avg_exam_score": avg_exam_score,
        "stuck_students": stuck_students,
        "enrollments_per_week": enrollments_per_week,
        "completions_per_course": completions_per_course,
    }
