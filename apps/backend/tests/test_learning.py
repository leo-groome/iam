from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_URL = "sqlite+aiosqlite:///./test_learning.db"

FAKE_SUB = "neon_learning_user_001"
FAKE_EMAIL = "learning@example.com"
FAKE_NAME = "Learning User"
HEADERS = {"Authorization": "Bearer fake-token"}


def _make_claims(**overrides):
    from app.security.neon_auth import StackAuthClaims

    return StackAuthClaims(
        sub=overrides.get("sub", FAKE_SUB),
        email=overrides.get("email", FAKE_EMAIL),
        name=overrides.get("name", FAKE_NAME),
    )


def _mock_verify(claims=None):
    return AsyncMock(return_value=claims or _make_claims())


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
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(engine) -> AsyncGenerator[AsyncClient, None]:
    import app.db as _db_module
    from app.main import app

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    app.dependency_overrides[_db_module.get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Fixtures: course with 2 modules, 2 topics each ─────────────────────


@pytest_asyncio.fixture
async def scaffold(db_session: AsyncSession):
    from app.models.base import new_uuid
    from app.models.course import Course, Module, Topic
    from app.models.progress import Enrollment
    from app.models.question import Option, Question
    from app.models.user import User

    user = User(
        id=new_uuid(),
        neon_user_id=FAKE_SUB,
        email=FAKE_EMAIL,
        full_name=FAKE_NAME,
        birth_date=_birth_date_age(25),
        role="estudiante",
        status="activo",
    )
    db_session.add(user)

    course = Course(
        id=new_uuid(),
        slug="learn-course",
        title="Learn Course",
        short_desc="",
        long_desc="",
        order_index=0,
        status="publicado",
    )
    db_session.add(course)
    await db_session.flush()

    mod1 = Module(id=new_uuid(), course_id=course.id, title="Module 1", order_index=0)
    mod2 = Module(id=new_uuid(), course_id=course.id, title="Module 2", order_index=1)
    db_session.add_all([mod1, mod2])
    await db_session.flush()

    t1 = Topic(
        id=new_uuid(), module_id=mod1.id, title="Topic 1", content_type="video",
        duration_seconds=120, has_exam=True, exam_min_score=70, order_index=0
    )
    t2 = Topic(
        id=new_uuid(), module_id=mod1.id, title="Topic 2", content_type="texto",
        has_exam=True, exam_min_score=70, order_index=1
    )
    t3 = Topic(
        id=new_uuid(), module_id=mod2.id, title="Topic 3", content_type="video",
        duration_seconds=120, has_exam=True, exam_min_score=70, order_index=0
    )
    t4 = Topic(
        id=new_uuid(), module_id=mod2.id, title="Topic 4", content_type="texto",
        has_exam=True, exam_min_score=70, order_index=1
    )
    db_session.add_all([t1, t2, t3, t4])
    await db_session.flush()

    # Questions for t1 and t2
    for topic in [t1, t2]:
        q = Question(id=new_uuid(), topic_id=topic.id, enunciado="Test question?")
        db_session.add(q)
        await db_session.flush()
        opt_correct = Option(id=new_uuid(), question_id=q.id, texto="Correct", is_correct=True, order_index=0)
        opt_wrong = Option(id=new_uuid(), question_id=q.id, texto="Wrong", is_correct=False, order_index=1)
        db_session.add_all([opt_correct, opt_wrong])

    # Module 1 exam question
    mq = Question(id=new_uuid(), module_id=mod1.id, enunciado="Module question?")
    db_session.add(mq)
    await db_session.flush()
    mopt_c = Option(id=new_uuid(), question_id=mq.id, texto="Correct", is_correct=True, order_index=0)
    mopt_w = Option(id=new_uuid(), question_id=mq.id, texto="Wrong", is_correct=False, order_index=1)
    db_session.add_all([mopt_c, mopt_w])

    enrollment = Enrollment(
        id=new_uuid(),
        user_id=user.id,
        course_id=course.id,
        started_at=datetime.now(UTC),
    )
    db_session.add(enrollment)

    await db_session.commit()
    await db_session.refresh(t1)
    await db_session.refresh(t2)
    await db_session.refresh(t3)
    await db_session.refresh(t4)
    await db_session.refresh(mod1)
    await db_session.refresh(mod2)

    return {
        "user": user,
        "course": course,
        "mod1": mod1,
        "mod2": mod2,
        "t1": t1,
        "t2": t2,
        "t3": t3,
        "t4": t4,
    }


# ─── Topic locked → 403 ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_topic_locked_returns_403(client: AsyncClient, scaffold):
    t2 = scaffold["t2"]
    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.get(f"/api/v1/topics/{t2.id}", headers=HEADERS)
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "topic_locked"


@pytest.mark.asyncio
async def test_first_topic_is_available(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]
    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.get(f"/api/v1/topics/{t1.id}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["state"] == "disponible"


# ─── Heartbeat: video_max_seen_pct never decreases ───────────────────────


@pytest.mark.asyncio
async def test_heartbeat_monotonic_max_seen_pct(client: AsyncClient, scaffold, db_session: AsyncSession):
    t1 = scaffold["t1"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        # Set to 50
        r1 = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 60, "max_seen_pct": 50},
            headers=HEADERS,
        )
        assert r1.status_code == 200
        assert r1.json()["video_max_seen_pct"] == 50

        # Adversarial: try to decrease to 10 — must stay at 50
        r2 = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 10, "max_seen_pct": 10},
            headers=HEADERS,
        )
        assert r2.status_code == 200
        assert r2.json()["video_max_seen_pct"] == 50


# ─── mark-content-done: video < 95% fails ────────────────────────────────


@pytest.mark.asyncio
async def test_heartbeat_ignores_claimed_video_jump(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 1, "max_seen_pct": 95},
            headers=HEADERS,
        )
        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["video_max_seen_pct"] == 1
    assert resp.json()["state"] == "disponible"
    assert exam_resp.status_code == 403


@pytest.mark.asyncio
async def test_mark_content_done_video_below_95_fails(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 90, "max_seen_pct": 80},
            headers=HEADERS,
        )
        resp = await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "content_incomplete"


@pytest.mark.asyncio
async def test_mark_content_done_video_at_95_succeeds(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 120, "max_seen_pct": 95},
            headers=HEADERS,
        )
        resp = await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["state"] == "contenido_visto"


@pytest.mark.asyncio
async def test_video_heartbeat_at_95_marks_content_seen(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )
        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["state"] == "contenido_visto"
    assert exam_resp.status_code == 200


# ─── Exam: submit fail → en_repaso, video_max_seen_pct = 0 ───────────────


@pytest.mark.asyncio
async def test_exam_fail_sets_en_repaso_and_resets_progress(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    from sqlalchemy import select

    from app.models.progress import TopicProgress

    t1 = scaffold["t1"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        # First get to contenido_visto
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )
        await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

        # Get exam
        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)
        assert exam_resp.status_code == 200
        exam = exam_resp.json()
        questions = exam["questions"]

        # Submit all wrong answers
        wrong_option = next(o for o in questions[0]["options"] if o["texto"] == "Wrong")
        answers = [{"question_id": questions[0]["id"], "option_id": wrong_option["id"]}]

        result = await client.post(
            f"/api/v1/topics/{t1.id}/exam/submit",
            json={"exam_token": exam["exam_token"], "answers": answers},
            headers=HEADERS,
        )

    assert result.status_code == 200
    data = result.json()
    assert data["passed"] is False

    tp_result = await db_session.execute(
        select(TopicProgress).where(TopicProgress.topic_id == t1.id)
    )
    tp = tp_result.scalar_one_or_none()
    assert tp is not None
    assert tp.state == "en_repaso"
    assert tp.video_max_seen_pct == 0


# ─── Exam: submit pass → aprobado, progress recomputed ───────────────────


@pytest.mark.asyncio
async def test_exam_pass_sets_aprobado_and_updates_progress(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    from sqlalchemy import select

    from app.models.progress import Enrollment, TopicProgress

    t1 = scaffold["t1"]
    course = scaffold["course"]
    user = scaffold["user"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )
        await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)
        exam = exam_resp.json()
        questions = exam["questions"]

        correct_option = next(o for o in questions[0]["options"] if o["texto"] == "Correct")
        answers = [{"question_id": questions[0]["id"], "option_id": correct_option["id"]}]

        result = await client.post(
            f"/api/v1/topics/{t1.id}/exam/submit",
            json={"exam_token": exam["exam_token"], "answers": answers},
            headers=HEADERS,
        )

    assert result.status_code == 200
    assert result.json()["passed"] is True

    tp_result = await db_session.execute(
        select(TopicProgress).where(
            TopicProgress.user_id == user.id,
            TopicProgress.topic_id == t1.id,
        )
    )
    tp = tp_result.scalar_one()
    assert tp.state == "aprobado"

    enr_result = await db_session.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course.id,
        )
    )
    enr = enr_result.scalar_one()
    assert enr.progress_cached > 0


# ─── 3 consecutive failures → user.status = atorado ─────────────────────


@pytest.mark.asyncio
async def test_exam_submit_requires_valid_exam_token(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )
        await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)
        question = exam_resp.json()["questions"][0]
        correct_option = next(o for o in question["options"] if o["texto"] == "Correct")

        result = await client.post(
            f"/api/v1/topics/{t1.id}/exam/submit",
            json={
                "exam_token": "not-a-valid-token",
                "answers": [
                    {"question_id": question["id"], "option_id": correct_option["id"]}
                ],
            },
            headers=HEADERS,
        )

    assert result.status_code == 403
    assert result.json()["detail"]["code"] == "invalid_exam_token"


@pytest.mark.asyncio
async def test_exam_submit_rejects_replayed_exam_token(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )
        await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)
        exam = exam_resp.json()
        question = exam["questions"][0]
        correct_option = next(o for o in question["options"] if o["texto"] == "Correct")
        payload = {
            "exam_token": exam["exam_token"],
            "answers": [{"question_id": question["id"], "option_id": correct_option["id"]}],
        }

        first = await client.post(
            f"/api/v1/topics/{t1.id}/exam/submit",
            json=payload,
            headers=HEADERS,
        )
        replay = await client.post(
            f"/api/v1/topics/{t1.id}/exam/submit",
            json=payload,
            headers=HEADERS,
        )

    assert first.status_code == 200
    assert replay.status_code == 409
    assert replay.json()["detail"]["code"] == "exam_token_replayed"


@pytest.mark.asyncio
async def test_exam_submit_rejects_option_for_other_question(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    from app.models.base import new_uuid
    from app.models.question import Option, Question

    t1 = scaffold["t1"]
    q = Question(id=new_uuid(), topic_id=t1.id, enunciado="Second question?")
    db_session.add(q)
    await db_session.flush()
    other_option = Option(
        id=new_uuid(),
        question_id=q.id,
        texto="Other",
        is_correct=True,
        order_index=0,
    )
    db_session.add(other_option)
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )
        await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)
        exam = exam_resp.json()
        first_question = next(
            question for question in exam["questions"] if question["id"] != str(q.id)
        )

        result = await client.post(
            f"/api/v1/topics/{t1.id}/exam/submit",
            json={
                "exam_token": exam["exam_token"],
                "answers": [
                    {"question_id": first_question["id"], "option_id": str(other_option.id)}
                ],
            },
            headers=HEADERS,
        )

    assert result.status_code == 422
    assert result.json()["detail"]["code"] == "invalid_option"


@pytest.mark.asyncio
async def test_three_consecutive_failures_sets_atorado(
    client: AsyncClient, scaffold, db_session: AsyncSession
):

    t1 = scaffold["t1"]
    user = scaffold["user"]

    async def do_fail_cycle():
        with patch("app.deps.verify_stack_token", _mock_verify()):
            # Reset content
            await client.post(
                f"/api/v1/topics/{t1.id}/heartbeat",
                json={"type": "video", "pos_seconds": 115, "max_seen_pct": 96},
                headers=HEADERS,
            )
            await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

            exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)
            exam = exam_resp.json()
            questions = exam["questions"]
            wrong_option = next(o for o in questions[0]["options"] if o["texto"] == "Wrong")
            answers = [{"question_id": questions[0]["id"], "option_id": wrong_option["id"]}]

            await client.post(
                f"/api/v1/topics/{t1.id}/exam/submit",
                json={"exam_token": exam["exam_token"], "answers": answers},
                headers=HEADERS,
            )

    for _ in range(3):
        await do_fail_cycle()

    await db_session.refresh(user)
    assert user.status == "atorado"


# ─── Module exam: blocked if any topic not approved ──────────────────────


@pytest.mark.asyncio
async def test_module_exam_blocked_if_topics_not_approved(client: AsyncClient, scaffold):
    mod1 = scaffold["mod1"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.get(f"/api/v1/modules/{mod1.id}/exam", headers=HEADERS)

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "module_topics_incomplete"


# ─── Topic in second module locked if module-exam of first not approved ──


@pytest.mark.asyncio
async def test_second_module_topic_locked_without_module_exam(
    client: AsyncClient, scaffold, db_session: AsyncSession
):

    from app.models.base import new_uuid
    from app.models.progress import TopicProgress

    t1 = scaffold["t1"]
    t2 = scaffold["t2"]
    t3 = scaffold["t3"]
    user = scaffold["user"]

    # Manually approve t1 and t2
    for t in [t1, t2]:
        tp = TopicProgress(
            id=new_uuid(),
            user_id=user.id,
            topic_id=t.id,
            state="aprobado",
        )
        db_session.add(tp)
    await db_session.commit()

    # t3 is in mod2 — mod1 has an exam, so t3 should be locked without mod1 exam passed
    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.get(f"/api/v1/topics/{t3.id}", headers=HEADERS)

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "topic_locked"
