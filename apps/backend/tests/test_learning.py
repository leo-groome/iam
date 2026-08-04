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
    from app.models.course import ContentBlock, Course, Module, Topic
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

    # Video content blocks — the new completion model gates on these, not on
    # legacy topic.content_type. t1 and t3 are video topics, so they each get
    # a single 'video' block matching the topic's admin-set duration.
    t1_block = ContentBlock(
        id=new_uuid(), topic_id=t1.id, kind="video", duration_seconds=120, order_index=0
    )
    t3_block = ContentBlock(
        id=new_uuid(), topic_id=t3.id, kind="video", duration_seconds=120, order_index=0
    )
    db_session.add_all([t1_block, t3_block])
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
    await db_session.refresh(t1_block)
    await db_session.refresh(t3_block)

    return {
        "user": user,
        "course": course,
        "mod1": mod1,
        "mod2": mod2,
        "t1": t1,
        "t2": t2,
        "t3": t3,
        "t4": t4,
        "t1_block": t1_block,
        "t3_block": t3_block,
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
    t1_block = scaffold["t1_block"]
    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.get(f"/api/v1/topics/{t1.id}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["state"] == "disponible"


# ─── Heartbeat: video_max_seen_pct never decreases ───────────────────────


@pytest.mark.asyncio
async def test_heartbeat_monotonic_max_seen_pct(client: AsyncClient, scaffold, db_session: AsyncSession):
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        # Set to 50
        r1 = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 60, "max_seen_pct": 50},
            headers=HEADERS,
        )
        assert r1.status_code == 200
        assert r1.json()["video_max_seen_pct"] == 50

        # Adversarial: try to decrease to 10 — must stay at 50
        r2 = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 10, "max_seen_pct": 10},
            headers=HEADERS,
        )
        assert r2.status_code == 200
        assert r2.json()["video_max_seen_pct"] == 50


# ─── mark-content-done: video < 95% fails ────────────────────────────────


@pytest.mark.asyncio
async def test_heartbeat_ignores_claimed_video_jump(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 1, "max_seen_pct": 95},
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
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 90, "max_seen_pct": 80},
            headers=HEADERS,
        )
        resp = await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "content_incomplete"


@pytest.mark.asyncio
async def test_mark_content_done_video_at_95_succeeds(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 120, "max_seen_pct": 95},
            headers=HEADERS,
        )
        resp = await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["state"] == "contenido_visto"


@pytest.mark.asyncio
async def test_mark_content_done_topic_without_video_blocks_succeeds_immediately(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    # Core semantics: only 'video' blocks gate completion. audio/pdf/imagen/texto
    # are complementary and never block — mark-content-done is honor-system for
    # topics that have no video block, even without any heartbeat call at all.
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]
    t1.content_type = "audio"
    t1.media_key = "audio/abc/leccion.mp3"
    t1_block.kind = "audio"
    t1_block.media_key = "audio/abc/leccion.mp3"
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["state"] == "contenido_visto"


@pytest.mark.asyncio
async def test_mark_content_done_pdf_block_gates_until_fully_read(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    # pdf blocks are now required (like video): mark-content-done must fail until
    # the heartbeat reports pdf_last_page >= pdf_total_pages, then succeed.
    from app.models.base import new_uuid
    from app.models.course import ContentBlock
    from app.models.progress import TopicProgress

    t1 = scaffold["t1"]
    t2 = scaffold["t2"]
    user = scaffold["user"]

    # Approve t1 first so t2 becomes available.
    tp1 = TopicProgress(id=new_uuid(), user_id=user.id, topic_id=t1.id, state="aprobado")
    db_session.add(tp1)

    pdf_block = ContentBlock(
        id=new_uuid(), topic_id=t2.id, kind="pdf", media_key="pdf/x/slides.pdf", order_index=0
    )
    db_session.add_all(
        [
            pdf_block,
            ContentBlock(
                id=new_uuid(), topic_id=t2.id, kind="texto", content_body="Texto.", order_index=1
            ),
        ]
    )
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        before = await client.post(f"/api/v1/topics/{t2.id}/mark-content-done", headers=HEADERS)

        await client.post(
            f"/api/v1/topics/{t2.id}/heartbeat",
            json={
                "type": "pdf",
                "block_id": str(pdf_block.id),
                "last_page": 3,
                "total_pages": 5,
            },
            headers=HEADERS,
        )
        partial = await client.post(f"/api/v1/topics/{t2.id}/mark-content-done", headers=HEADERS)

        await client.post(
            f"/api/v1/topics/{t2.id}/heartbeat",
            json={
                "type": "pdf",
                "block_id": str(pdf_block.id),
                "last_page": 5,
                "total_pages": 5,
            },
            headers=HEADERS,
        )
        after = await client.post(f"/api/v1/topics/{t2.id}/mark-content-done", headers=HEADERS)

    assert before.status_code == 422
    assert before.json()["detail"]["code"] == "content_incomplete"
    assert partial.status_code == 422
    assert partial.json()["detail"]["code"] == "content_incomplete"
    assert after.status_code == 200
    assert after.json()["state"] == "contenido_visto"


@pytest.mark.asyncio
async def test_mark_content_done_texto_only_topic_succeeds_immediately(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    # A topic with only a texto block (no video/pdf) has no required blocks and
    # passes mark-content-done unconditionally (honor-system).
    from app.models.base import new_uuid
    from app.models.course import ContentBlock
    from app.models.progress import TopicProgress

    t1 = scaffold["t1"]
    t2 = scaffold["t2"]
    user = scaffold["user"]

    tp1 = TopicProgress(id=new_uuid(), user_id=user.id, topic_id=t1.id, state="aprobado")
    db_session.add(tp1)

    db_session.add(
        ContentBlock(
            id=new_uuid(), topic_id=t2.id, kind="texto", content_body="Texto.", order_index=0
        )
    )
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(f"/api/v1/topics/{t2.id}/mark-content-done", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["state"] == "contenido_visto"


@pytest.mark.asyncio
async def test_mark_content_done_requires_both_video_and_pdf(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    # A topic with both a video and a pdf block requires both to be complete.
    from app.models.base import new_uuid
    from app.models.course import ContentBlock

    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]

    pdf_block = ContentBlock(
        id=new_uuid(), topic_id=t1.id, kind="pdf", media_key="pdf/x/slides.pdf", order_index=1
    )
    db_session.add(pdf_block)
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        # Only video complete — pdf still missing.
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )
        video_only = await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

        # Now complete pdf too.
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "pdf", "block_id": str(pdf_block.id), "last_page": 4, "total_pages": 4},
            headers=HEADERS,
        )
        both_done = await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

    assert video_only.status_code == 422
    assert video_only.json()["detail"]["code"] == "content_incomplete"
    assert both_done.status_code == 200
    assert both_done.json()["state"] == "contenido_visto"


@pytest.mark.asyncio
async def test_get_topic_returns_ordered_blocks_with_progress(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        # Heartbeat on the video block first so its progress is non-default.
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 60, "max_seen_pct": 50},
            headers=HEADERS,
        )
        resp = await client.get(f"/api/v1/topics/{t1.id}", headers=HEADERS)

    assert resp.status_code == 200
    blocks = resp.json()["blocks"]
    assert len(blocks) == 1
    assert blocks[0]["id"] == str(t1_block.id)
    assert blocks[0]["kind"] == "video"
    assert blocks[0]["progress"]["video_max_seen_pct"] == 50
    assert blocks[0]["progress"]["video_last_pos_seconds"] == 60
    assert blocks[0]["progress"]["completed"] is False


@pytest.mark.asyncio
async def test_mark_content_done_video_requires_minimum_watch_seconds(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]
    t1.duration_seconds = 4
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 4, "max_seen_pct": 100},
            headers=HEADERS,
        )
        resp = await client.post(f"/api/v1/topics/{t1.id}/mark-content-done", headers=HEADERS)

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "content_incomplete"


@pytest.mark.asyncio
async def test_video_heartbeat_at_95_marks_content_seen(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )
        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["state"] == "contenido_visto"
    assert exam_resp.status_code == 200


@pytest.mark.asyncio
async def test_video_heartbeat_db_duration_is_authoritative_over_client_report(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    # block.duration_seconds is auto-detected from the real media file on upload and
    # is authoritative for the completion % denominator. A client cannot shrink the
    # denominator by reporting a smaller duration_seconds in the heartbeat body to
    # fake a high percentage: real clip is 120s, client claims duration_seconds=10
    # at pos_seconds=10 (which would be a fake 100% if the client value won) — the
    # true pct against the DB duration is only ~8%, so content must stay locked.
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]
    t1_block.duration_seconds = 120
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={
                "type": "video",
                "block_id": str(t1_block.id),
                "pos_seconds": 10,
                "duration_seconds": 10,
                "max_seen_pct": 100,
            },
            headers=HEADERS,
        )
        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["state"] == "disponible"
    assert resp.json()["video_max_seen_pct"] == 8
    assert exam_resp.status_code == 403


@pytest.mark.asyncio
async def test_video_heartbeat_falls_back_to_client_duration_when_db_missing(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    # When the DB has no duration on record (e.g. a legacy block created before
    # auto-detection), the client-reported duration is used as a fallback so
    # completion can still be computed.
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]
    t1_block.duration_seconds = None
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={
                "type": "video",
                "block_id": str(t1_block.id),
                "pos_seconds": 115,
                "duration_seconds": 120,
                "max_seen_pct": 96,
            },
            headers=HEADERS,
        )
        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["state"] == "contenido_visto"
    assert exam_resp.status_code == 200


@pytest.mark.asyncio
async def test_video_heartbeat_min_seconds_floor_blocks_trivial_skip(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    # Even at 100% of a very short reported duration, the 5-second minimum-watch floor
    # keeps the content locked to prevent instant skips.
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={
                "type": "video",
                "block_id": str(t1_block.id),
                "pos_seconds": 3,
                "duration_seconds": 3,
                "max_seen_pct": 100,
            },
            headers=HEADERS,
        )
        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["state"] == "disponible"
    assert exam_resp.status_code == 403


@pytest.mark.asyncio
async def test_video_heartbeat_ignores_completed_client_pct_without_position_progress(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]
    t1_block.duration_seconds = 999
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 8, "max_seen_pct": 100},
            headers=HEADERS,
        )
        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["state"] == "disponible"
    assert resp.json()["video_max_seen_pct"] == 1
    assert exam_resp.status_code == 403


# ─── Exam: submit fail → en_repaso, video_max_seen_pct = 0 ───────────────


@pytest.mark.asyncio
async def test_exam_fail_sets_en_repaso_and_resets_progress(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    from sqlalchemy import select

    from app.models.progress import TopicProgress

    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        # First get to contenido_visto
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
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
async def test_exam_after_failure_requires_rewatch_before_retry(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )
        exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)
        exam = exam_resp.json()
        question = exam["questions"][0]
        wrong_option = next(o for o in question["options"] if o["texto"] == "Wrong")

        fail_resp = await client.post(
            f"/api/v1/topics/{t1.id}/exam/submit",
            json={
                "exam_token": exam["exam_token"],
                "answers": [{"question_id": question["id"], "option_id": wrong_option["id"]}],
            },
            headers=HEADERS,
        )
        retry_before_rewatch = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)

        rewatch = await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )
        retry_after_rewatch = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)

    assert fail_resp.status_code == 200
    assert fail_resp.json()["passed"] is False
    assert retry_before_rewatch.status_code == 403
    assert retry_before_rewatch.json()["detail"]["code"] == "repaso_required"
    assert rewatch.status_code == 200
    assert rewatch.json()["state"] == "contenido_visto"
    assert retry_after_rewatch.status_code == 200


@pytest.mark.asyncio
async def test_exam_submit_with_prefailure_token_requires_rewatch(client: AsyncClient, scaffold):
    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
            headers=HEADERS,
        )

        first_exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)
        second_exam_resp = await client.get(f"/api/v1/topics/{t1.id}/exam", headers=HEADERS)
        first_exam = first_exam_resp.json()
        second_exam = second_exam_resp.json()

        first_question = first_exam["questions"][0]
        first_wrong = next(o for o in first_question["options"] if o["texto"] == "Wrong")
        fail_resp = await client.post(
            f"/api/v1/topics/{t1.id}/exam/submit",
            json={
                "exam_token": first_exam["exam_token"],
                "answers": [{"question_id": first_question["id"], "option_id": first_wrong["id"]}],
            },
            headers=HEADERS,
        )

        second_question = second_exam["questions"][0]
        second_correct = next(o for o in second_question["options"] if o["texto"] == "Correct")
        stale_submit = await client.post(
            f"/api/v1/topics/{t1.id}/exam/submit",
            json={
                "exam_token": second_exam["exam_token"],
                "answers": [{"question_id": second_question["id"], "option_id": second_correct["id"]}],
            },
            headers=HEADERS,
        )

    assert fail_resp.status_code == 200
    assert fail_resp.json()["passed"] is False
    assert stale_submit.status_code == 403
    assert stale_submit.json()["detail"]["code"] == "repaso_required"


@pytest.mark.asyncio
async def test_exam_pass_sets_aprobado_and_updates_progress(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    from sqlalchemy import select

    from app.models.progress import Enrollment, TopicProgress

    t1 = scaffold["t1"]
    t1_block = scaffold["t1_block"]
    course = scaffold["course"]
    user = scaffold["user"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
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
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
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
    t1_block = scaffold["t1_block"]

    with patch("app.deps.verify_stack_token", _mock_verify()):
        await client.post(
            f"/api/v1/topics/{t1.id}/heartbeat",
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
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
    t1_block = scaffold["t1_block"]
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
            json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
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
    t1_block = scaffold["t1_block"]
    user = scaffold["user"]

    async def do_fail_cycle():
        with patch("app.deps.verify_stack_token", _mock_verify()):
            # Reset content
            await client.post(
                f"/api/v1/topics/{t1.id}/heartbeat",
                json={"type": "video", "block_id": str(t1_block.id), "pos_seconds": 115, "max_seen_pct": 96},
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
    t1_block = scaffold["t1_block"]
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
