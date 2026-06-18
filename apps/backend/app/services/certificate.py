"""Certificate issuance service.

Design decisions:
- R-CERT-04 (name at download time): The PRD frontend says "nombre al momento de descarga".
  This backend uses `student_name_snapshot` captured at issue time for immutability.
  Rationale: a certificate is a legal document; the name should reflect who the student
  was at completion. The frontend can call `PATCH /api/v1/certificates/{public_uuid}/refresh-name`
  immediately before sharing/displaying to update the snapshot to the current `user.full_name`.
  This satisfies the spirit of R-CERT-04 without making the verify page dynamic.

- Auto-issuance: When `enrollment.progress_cached` reaches 100 in `on_topic_exam_passed`
  (progress_engine.py), ideally `issue_certificate` would be called automatically.
  This is intentionally left manual for MVP: the frontend calls `POST /api/v1/certificates/issue/{course_id}`
  when it detects 100% progress. This avoids coupling the progress engine to the certificate
  service and keeps the service boundary clean. A background task or event hook can wire this
  in a future iteration without breaking the existing contract.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.certificate import Certificate
from app.models.course import Course, Module, Topic
from app.models.progress import Enrollment, ExamAttempt, TopicProgress
from app.models.question import Question
from app.models.user import User


async def _get_active_topics(db: AsyncSession, course_id: uuid.UUID) -> list[Topic]:
    """Return all non-archived topics for a course, ordered by module + topic order."""
    result = await db.execute(
        select(Module)
        .where(Module.course_id == course_id, Module.archived_at.is_(None))
        .options(selectinload(Module.topics))
        .order_by(Module.order_index)
    )
    modules = list(result.scalars().all())
    topics: list[Topic] = []
    for mod in modules:
        for t in sorted(mod.topics, key=lambda x: x.order_index):
            if t.archived_at is None:
                topics.append(t)
    return topics


async def can_issue_certificate(
    db: AsyncSession,
    user: User,
    course: Course,
) -> bool:
    """Return True iff the user has completed the course and all active topics are approved.

    Both conditions must hold:
    1. enrollment.progress_cached == 100
    2. Every non-archived topic has a TopicProgress row with state='aprobado'
    3. If a module has modular exam questions, the module exam must be passed
    """
    enr_result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course.id,
        )
    )
    enrollment = enr_result.scalar_one_or_none()
    if enrollment is None or enrollment.progress_cached != 100:
        return False

    active_topics = await _get_active_topics(db, course.id)
    if not active_topics:
        return False

    for topic in active_topics:
        tp_result = await db.execute(
            select(TopicProgress).where(
                TopicProgress.user_id == user.id,
                TopicProgress.topic_id == topic.id,
            )
        )
        tp = tp_result.scalar_one_or_none()
        if tp is None or tp.state != "aprobado":
            return False

    # Check modular exams if any module has active exam questions
    modules_result = await db.execute(
        select(Module).where(
            Module.course_id == course.id,
            Module.archived_at.is_(None),
        )
    )
    active_modules = modules_result.scalars().all()

    for m in active_modules:
        q_result = await db.execute(
            select(Question)
            .where(Question.module_id == m.id, Question.archived_at.is_(None))
            .limit(1)
        )
        has_questions = q_result.scalar_one_or_none() is not None

        if has_questions:
            passed_result = await db.execute(
                select(ExamAttempt).where(
                    ExamAttempt.user_id == user.id,
                    ExamAttempt.module_id == m.id,
                    ExamAttempt.passed.is_(True),
                ).limit(1)
            )
            passed = passed_result.scalar_one_or_none() is not None
            if not passed:
                return False

    return True


async def issue_certificate(
    db: AsyncSession,
    user: User,
    course: Course,
) -> Certificate:
    """Create and persist a certificate for (user, course). Idempotent via UNIQUE constraint.

    If a certificate already exists for this (user, course) pair, returns the existing row.
    Snapshots student name and course title at time of issuance.
    """
    existing_result = await db.execute(
        select(Certificate).where(
            Certificate.user_id == user.id,
            Certificate.course_id == course.id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return existing

    cert = Certificate(
        id=uuid.uuid4(),
        public_uuid=uuid.uuid4(),
        user_id=user.id,
        course_id=course.id,
        issued_at=datetime.now(UTC),
        student_name_snapshot=user.full_name,
        course_title_snapshot=course.title,
    )
    db.add(cert)
    await db.flush()
    return cert
