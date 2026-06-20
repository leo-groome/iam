from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_URL = "sqlite+aiosqlite:///./test_progress_engine.db"


def _birth_date_age(age: int) -> date:
    today = date.today()
    return date(today.year - age, today.month, today.day)


@pytest_asyncio.fixture(scope="function")
async def engine():
    from app.models.base import Base

    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def scaffold(db: AsyncSession):
    from app.models.base import new_uuid
    from app.models.course import Course, Module, Topic
    from app.models.progress import Enrollment
    from app.models.user import User

    user = User(
        id=new_uuid(),
        neon_user_id="test_engine_user",
        email="engine@test.com",
        full_name="Engine User",
        birth_date=_birth_date_age(25),
        role="estudiante",
        status="activo",
    )
    db.add(user)

    course = Course(
        id=new_uuid(), slug="engine-course", title="Engine Course",
        short_desc="", long_desc="", order_index=0, status="publicado",
    )
    db.add(course)
    await db.flush()

    mod1 = Module(id=new_uuid(), course_id=course.id, title="Mod1", order_index=0)
    mod2 = Module(id=new_uuid(), course_id=course.id, title="Mod2", order_index=1)
    db.add_all([mod1, mod2])
    await db.flush()

    t1 = Topic(id=new_uuid(), module_id=mod1.id, title="T1", content_type="video",
               has_exam=True, exam_min_score=70, order_index=0)
    t2 = Topic(id=new_uuid(), module_id=mod1.id, title="T2", content_type="texto",
               has_exam=True, exam_min_score=70, order_index=1)
    t3 = Topic(id=new_uuid(), module_id=mod2.id, title="T3", content_type="video",
               has_exam=True, exam_min_score=70, order_index=0)
    db.add_all([t1, t2, t3])

    enrollment = Enrollment(
        id=new_uuid(), user_id=user.id, course_id=course.id,
        started_at=datetime.now(UTC),
    )
    db.add(enrollment)
    await db.commit()

    for obj in [t1, t2, t3, mod1, mod2]:
        await db.refresh(obj)

    return {"user": user, "course": course, "mod1": mod1, "mod2": mod2, "t1": t1, "t2": t2, "t3": t3}


# ─── compute_topic_state ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_first_topic_disponible(db: AsyncSession, scaffold):
    from app.services.progress_engine import compute_topic_state

    t1 = scaffold["t1"]
    user = scaffold["user"]
    state = await compute_topic_state(db, user, t1)
    assert state == "disponible"


@pytest.mark.asyncio
async def test_second_topic_locked_without_first_approved(db: AsyncSession, scaffold):
    from app.services.progress_engine import compute_topic_state

    t2 = scaffold["t2"]
    user = scaffold["user"]
    state = await compute_topic_state(db, user, t2)
    assert state == "bloqueado"


@pytest.mark.asyncio
async def test_second_topic_available_after_first_approved(db: AsyncSession, scaffold):
    from app.models.base import new_uuid
    from app.models.progress import TopicProgress
    from app.services.progress_engine import compute_topic_state

    t1 = scaffold["t1"]
    t2 = scaffold["t2"]
    user = scaffold["user"]

    tp = TopicProgress(id=new_uuid(), user_id=user.id, topic_id=t1.id, state="aprobado")
    db.add(tp)
    await db.commit()
    await db.refresh(t2)

    state = await compute_topic_state(db, user, t2)
    assert state == "disponible"


@pytest.mark.asyncio
async def test_second_module_first_topic_locked_without_mod_exam(db: AsyncSession, scaffold):
    from app.models.base import new_uuid
    from app.models.progress import TopicProgress
    from app.models.question import Option, Question
    from app.services.progress_engine import compute_topic_state

    t1 = scaffold["t1"]
    t2 = scaffold["t2"]
    t3 = scaffold["t3"]
    mod1 = scaffold["mod1"]
    user = scaffold["user"]

    # Add a module exam question so module exam is required
    q = Question(id=new_uuid(), module_id=mod1.id, enunciado="Mod Q?")
    db.add(q)
    await db.flush()
    db.add(Option(id=new_uuid(), question_id=q.id, texto="A", is_correct=True, order_index=0))

    # Approve t1 and t2
    for t in [t1, t2]:
        tp = TopicProgress(id=new_uuid(), user_id=user.id, topic_id=t.id, state="aprobado")
        db.add(tp)
    await db.commit()

    # t3 should be locked — mod1 exam not yet passed
    await db.refresh(t3)
    state = await compute_topic_state(db, user, t3)
    assert state == "bloqueado"


@pytest.mark.asyncio
async def test_second_module_first_topic_available_after_mod_exam(db: AsyncSession, scaffold):
    from app.models.base import new_uuid
    from app.models.progress import ExamAttempt, TopicProgress
    from app.models.question import Option, Question
    from app.services.progress_engine import compute_topic_state

    t1 = scaffold["t1"]
    t2 = scaffold["t2"]
    t3 = scaffold["t3"]
    mod1 = scaffold["mod1"]
    user = scaffold["user"]

    q = Question(id=new_uuid(), module_id=mod1.id, enunciado="Mod Q?")
    db.add(q)
    await db.flush()
    db.add(Option(id=new_uuid(), question_id=q.id, texto="A", is_correct=True, order_index=0))

    for t in [t1, t2]:
        tp = TopicProgress(id=new_uuid(), user_id=user.id, topic_id=t.id, state="aprobado")
        db.add(tp)

    attempt = ExamAttempt(
        id=new_uuid(),
        user_id=user.id,
        module_id=mod1.id,
        topic_id=None,
        score=80,
        passed=True,
        min_score_snapshot=70,
        answers={},
        created_at=datetime.now(UTC),
    )
    db.add(attempt)
    await db.commit()

    await db.refresh(t3)
    state = await compute_topic_state(db, user, t3)
    assert state == "disponible"


@pytest.mark.asyncio
async def test_second_module_no_mod_exam_unlocks_automatically(db: AsyncSession, scaffold):
    from app.models.base import new_uuid
    from app.models.progress import TopicProgress
    from app.services.progress_engine import compute_topic_state

    t1 = scaffold["t1"]
    t2 = scaffold["t2"]
    t3 = scaffold["t3"]
    user = scaffold["user"]

    # No module exam questions — approving all topics is enough
    for t in [t1, t2]:
        tp = TopicProgress(id=new_uuid(), user_id=user.id, topic_id=t.id, state="aprobado")
        db.add(tp)
    await db.commit()

    await db.refresh(t3)
    state = await compute_topic_state(db, user, t3)
    assert state == "disponible"


# ─── recompute_course_progress ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_recompute_course_progress_partial(db: AsyncSession, scaffold):
    from app.models.base import new_uuid
    from app.models.progress import TopicProgress
    from app.services.progress_engine import recompute_course_progress

    t1 = scaffold["t1"]
    user = scaffold["user"]
    course = scaffold["course"]

    tp = TopicProgress(id=new_uuid(), user_id=user.id, topic_id=t1.id, state="aprobado")
    db.add(tp)
    await db.commit()

    pct = await recompute_course_progress(db, user, course)
    assert 0 < pct < 100


@pytest.mark.asyncio
async def test_recompute_course_progress_full(db: AsyncSession, scaffold):
    from app.models.base import new_uuid
    from app.models.progress import TopicProgress
    from app.services.progress_engine import recompute_course_progress

    t1 = scaffold["t1"]
    t2 = scaffold["t2"]
    t3 = scaffold["t3"]
    user = scaffold["user"]
    course = scaffold["course"]

    for t in [t1, t2, t3]:
        tp = TopicProgress(id=new_uuid(), user_id=user.id, topic_id=t.id, state="aprobado")
        db.add(tp)
    await db.commit()

    pct = await recompute_course_progress(db, user, course)
    assert pct == 100


# ─── on_topic_exam_passed / failed ───────────────────────────────────────


@pytest.mark.asyncio
async def test_on_topic_exam_passed_state_and_progress(db: AsyncSession, scaffold):
    from app.models.base import new_uuid
    from app.models.progress import TopicProgress
    from app.services.progress_engine import on_topic_exam_passed

    t1 = scaffold["t1"]
    user = scaffold["user"]

    tp = TopicProgress(id=new_uuid(), user_id=user.id, topic_id=t1.id, state="contenido_visto",
                       video_max_seen_pct=96)
    db.add(tp)
    await db.commit()
    await db.refresh(t1)

    await on_topic_exam_passed(db, user, t1, tp)
    await db.commit()
    await db.refresh(tp)

    assert tp.state == "aprobado"


@pytest.mark.asyncio
async def test_on_topic_exam_failed_resets_trackers(db: AsyncSession, scaffold):
    from app.models.base import new_uuid
    from app.models.progress import TopicProgress
    from app.services.progress_engine import on_topic_exam_failed

    t1 = scaffold["t1"]
    user = scaffold["user"]

    now = datetime.now(UTC)
    tp = TopicProgress(
        id=new_uuid(), user_id=user.id, topic_id=t1.id, state="contenido_visto",
        video_max_seen_pct=96, pdf_last_page=5, content_completed_at=now,
    )
    db.add(tp)
    await db.commit()
    await db.refresh(t1)

    await on_topic_exam_failed(db, user, t1, tp)
    await db.commit()
    await db.refresh(tp)

    assert tp.state == "en_repaso"
    assert tp.video_max_seen_pct == 0
    assert tp.pdf_last_page == 0
    assert tp.content_completed_at is None


# ─── check_user_status ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_user_status_atorado_after_3_failures(db: AsyncSession, scaffold):
    from app.models.base import new_uuid
    from app.models.progress import ExamAttempt
    from app.services.progress_engine import check_user_status

    t1 = scaffold["t1"]
    user = scaffold["user"]

    for _ in range(3):
        attempt = ExamAttempt(
            id=new_uuid(), user_id=user.id, topic_id=t1.id, module_id=None,
            score=40, passed=False, min_score_snapshot=70, answers={},
            created_at=datetime.now(UTC),
        )
        db.add(attempt)
    await db.commit()

    await check_user_status(db, user, t1.id)
    await db.commit()
    await db.refresh(user)

    assert user.status == "atorado"


@pytest.mark.asyncio
async def test_check_user_status_not_atorado_after_pass(db: AsyncSession, scaffold):
    from app.models.base import new_uuid
    from app.models.progress import ExamAttempt
    from app.services.progress_engine import check_user_status

    t1 = scaffold["t1"]
    user = scaffold["user"]

    # 2 failures then 1 pass — streak broken
    for _ in range(2):
        attempt = ExamAttempt(
            id=new_uuid(), user_id=user.id, topic_id=t1.id, module_id=None,
            score=40, passed=False, min_score_snapshot=70, answers={},
            created_at=datetime.now(UTC),
        )
        db.add(attempt)
    passed_attempt = ExamAttempt(
        id=new_uuid(), user_id=user.id, topic_id=t1.id, module_id=None,
        score=80, passed=True, min_score_snapshot=70, answers={},
        created_at=datetime.now(UTC),
    )
    db.add(passed_attempt)
    await db.commit()

    await check_user_status(db, user, t1.id)
    await db.commit()
    await db.refresh(user)

    assert user.status != "atorado"
