"""Tests for certificate issuance, retrieval, verify page, and name refresh.

Coverage:
- Issue with incomplete course → 422 course_incomplete
- Issue with 100% progress → 201, certificate created with correct snapshots
- Issue idempotent: second POST returns same certificate (same public_uuid)
- GET /api/v1/certificates/{uuid} without auth → 200
- GET /verify/{uuid} → 200 HTML with student name, course title, QR <img>
- HTML verify includes data URI QR code
- 404 for unknown UUID on both endpoints
- PATCH refresh-name: owner succeeds, non-owner → 403
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_URL = "sqlite+aiosqlite:///./test_certificates.db"

FAKE_SUB = "neon_cert_user_001"
FAKE_EMAIL = "cert@example.com"
FAKE_NAME = "Cert Student"
OTHER_SUB = "neon_cert_other_002"
OTHER_EMAIL = "other@example.com"
OTHER_NAME = "Other User"
HEADERS = {"Authorization": "Bearer fake-token"}
OTHER_HEADERS = {"Authorization": "Bearer fake-other-token"}


def _make_claims(sub: str = FAKE_SUB, email: str = FAKE_EMAIL, name: str = FAKE_NAME):
    from app.security.neon_auth import StackAuthClaims
    return StackAuthClaims(sub=sub, email=email, name=name)


def _mock_verify(sub: str = FAKE_SUB, email: str = FAKE_EMAIL, name: str = FAKE_NAME):
    return AsyncMock(return_value=_make_claims(sub=sub, email=email, name=name))


def _birth_date_age(age: int) -> date:
    today = date.today()
    return date(today.year - age, today.month, today.day)


# ── Fixtures ──────────────────────────────────────────────────────────────────


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


@pytest_asyncio.fixture
async def scaffold(db_session: AsyncSession):
    """
    Creates:
    - user (main, 100% complete)
    - other_user (secondary, for ownership tests)
    - course with 1 module, 1 topic
    - enrollment with progress_cached=100
    - TopicProgress state='aprobado' for the topic
    """
    from app.models.base import new_uuid
    from app.models.course import Course, Module, Topic
    from app.models.progress import Enrollment, TopicProgress
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
    other_user = User(
        id=new_uuid(),
        neon_user_id=OTHER_SUB,
        email=OTHER_EMAIL,
        full_name=OTHER_NAME,
        birth_date=_birth_date_age(22),
        role="estudiante",
        status="activo",
    )
    db_session.add_all([user, other_user])

    course = Course(
        id=new_uuid(),
        slug="cert-course",
        title="Cert Course Title",
        short_desc="",
        long_desc="",
        order_index=0,
        status="publicado",
    )
    db_session.add(course)
    await db_session.flush()

    mod = Module(id=new_uuid(), course_id=course.id, title="Module 1", order_index=0)
    db_session.add(mod)
    await db_session.flush()

    topic = Topic(
        id=new_uuid(),
        module_id=mod.id,
        title="Topic 1",
        content_type="video",
        has_exam=True,
        exam_min_score=70,
        order_index=0,
    )
    db_session.add(topic)
    await db_session.flush()

    enrollment = Enrollment(
        id=new_uuid(),
        user_id=user.id,
        course_id=course.id,
        started_at=datetime.now(UTC),
        progress_cached=100,
        completed_at=datetime.now(UTC),
    )
    db_session.add(enrollment)

    tp = TopicProgress(
        id=new_uuid(),
        user_id=user.id,
        topic_id=topic.id,
        state="aprobado",
    )
    db_session.add(tp)

    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(other_user)
    await db_session.refresh(course)
    await db_session.refresh(topic)

    return {
        "user": user,
        "other_user": other_user,
        "course": course,
        "topic": topic,
    }


@pytest_asyncio.fixture
async def scaffold_incomplete(db_session: AsyncSession):
    """Course with 0% progress — cannot issue certificate."""
    from app.models.base import new_uuid
    from app.models.course import Course, Module, Topic
    from app.models.progress import Enrollment
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
        slug="incomplete-course",
        title="Incomplete Course",
        short_desc="",
        long_desc="",
        order_index=0,
        status="publicado",
    )
    db_session.add(course)
    await db_session.flush()

    mod = Module(id=new_uuid(), course_id=course.id, title="Module 1", order_index=0)
    db_session.add(mod)
    await db_session.flush()

    topic = Topic(
        id=new_uuid(),
        module_id=mod.id,
        title="Topic 1",
        content_type="video",
        has_exam=True,
        exam_min_score=70,
        order_index=0,
    )
    db_session.add(topic)

    enrollment = Enrollment(
        id=new_uuid(),
        user_id=user.id,
        course_id=course.id,
        started_at=datetime.now(UTC),
        progress_cached=50,  # Not complete
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(course)

    return {"user": user, "course": course}


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_issue_incomplete_course_returns_422(client: AsyncClient, scaffold_incomplete):
    course = scaffold_incomplete["course"]
    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/certificates/issue/{course.id}",
            headers=HEADERS,
        )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "course_incomplete"


@pytest.mark.asyncio
async def test_issue_complete_course_returns_201(client: AsyncClient, scaffold):
    course = scaffold["course"]
    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/certificates/issue/{course.id}",
            headers=HEADERS,
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["course_title"] == "Cert Course Title"
    assert data["student_name"] == FAKE_NAME
    assert "public_uuid" in data
    assert data["verify_url"].endswith(f"/verify/{data['public_uuid']}")


@pytest.mark.asyncio
async def test_issue_idempotent_returns_same_certificate(client: AsyncClient, scaffold):
    """Two POST calls must return the same public_uuid (UNIQUE constraint on user+course)."""
    course = scaffold["course"]
    with patch("app.deps.verify_stack_token", _mock_verify()):
        r1 = await client.post(f"/api/v1/certificates/issue/{course.id}", headers=HEADERS)
        r2 = await client.post(f"/api/v1/certificates/issue/{course.id}", headers=HEADERS)

    assert r1.status_code == 201
    # Second call: still 201 (idempotent — we return existing cert)
    assert r2.status_code == 201
    assert r1.json()["public_uuid"] == r2.json()["public_uuid"]


@pytest.mark.asyncio
async def test_get_certificate_no_auth_returns_200(client: AsyncClient, scaffold):
    """GET /api/v1/certificates/{uuid} is auth-optional — must work without a token."""
    course = scaffold["course"]
    # First issue the cert
    with patch("app.deps.verify_stack_token", _mock_verify()):
        issue_resp = await client.post(f"/api/v1/certificates/issue/{course.id}", headers=HEADERS)
    assert issue_resp.status_code == 201
    public_uuid = issue_resp.json()["public_uuid"]

    # Now GET without any Authorization header
    resp = await client.get(f"/api/v1/certificates/{public_uuid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["public_uuid"] == public_uuid
    assert data["student_name"] == FAKE_NAME


@pytest.mark.asyncio
async def test_get_certificate_unknown_uuid_returns_404(client: AsyncClient):
    unknown = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/certificates/{unknown}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_verify_page_renders_html(client: AsyncClient, scaffold):
    """GET /verify/{uuid} must return HTML 200 with correct content."""
    course = scaffold["course"]
    with patch("app.deps.verify_stack_token", _mock_verify()):
        issue_resp = await client.post(f"/api/v1/certificates/issue/{course.id}", headers=HEADERS)
    assert issue_resp.status_code == 201
    public_uuid = issue_resp.json()["public_uuid"]

    resp = await client.get(f"/verify/{public_uuid}")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    html = resp.text
    assert FAKE_NAME in html
    assert "Cert Course Title" in html
    # Cache headers
    assert "public" in resp.headers.get("cache-control", "")
    assert "max-age=3600" in resp.headers.get("cache-control", "")
    assert resp.headers.get("x-robots-tag") == "index, follow"


@pytest.mark.asyncio
async def test_verify_page_contains_qr_data_uri(client: AsyncClient, scaffold):
    """HTML verify page must embed QR as a data URI <img>."""
    course = scaffold["course"]
    with patch("app.deps.verify_stack_token", _mock_verify()):
        issue_resp = await client.post(f"/api/v1/certificates/issue/{course.id}", headers=HEADERS)
    public_uuid = issue_resp.json()["public_uuid"]

    resp = await client.get(f"/verify/{public_uuid}")
    assert resp.status_code == 200
    assert 'data:image/png;base64,' in resp.text


@pytest.mark.asyncio
async def test_verify_page_unknown_uuid_returns_404(client: AsyncClient):
    unknown = str(uuid.uuid4())
    resp = await client.get(f"/verify/{unknown}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_refresh_name_owner_succeeds(client: AsyncClient, scaffold, db_session: AsyncSession):
    """PATCH /certificates/{uuid}/refresh-name updates the snapshot for the owner."""
    from sqlalchemy import select

    from app.models.certificate import Certificate as CertModel

    course = scaffold["course"]
    with patch("app.deps.verify_stack_token", _mock_verify()):
        issue_resp = await client.post(f"/api/v1/certificates/issue/{course.id}", headers=HEADERS)
    assert issue_resp.status_code == 201
    public_uuid = issue_resp.json()["public_uuid"]

    # Simulate user changing their name — update directly in DB to mimic full_name change
    user = scaffold["user"]
    user.full_name = "Cert Student Updated"
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify(name="Cert Student Updated")):
        resp = await client.patch(
            f"/api/v1/certificates/{public_uuid}/refresh-name",
            headers=HEADERS,
        )

    assert resp.status_code == 200
    assert resp.json()["student_name"] == "Cert Student Updated"

    # Verify persisted in DB
    result = await db_session.execute(
        select(CertModel).where(CertModel.public_uuid == uuid.UUID(public_uuid))
    )
    cert = result.scalar_one()
    assert cert.student_name_snapshot == "Cert Student Updated"


@pytest.mark.asyncio
async def test_refresh_name_non_owner_returns_403(client: AsyncClient, scaffold):
    """A different authenticated user cannot refresh the name on someone else's cert."""
    course = scaffold["course"]
    # Issue cert as main user
    with patch("app.deps.verify_stack_token", _mock_verify()):
        issue_resp = await client.post(f"/api/v1/certificates/issue/{course.id}", headers=HEADERS)
    assert issue_resp.status_code == 201
    public_uuid = issue_resp.json()["public_uuid"]

    # Try to refresh as other_user
    with patch(
        "app.deps.verify_stack_token",
        _mock_verify(sub=OTHER_SUB, email=OTHER_EMAIL, name=OTHER_NAME),
    ):
        resp = await client.patch(
            f"/api/v1/certificates/{public_uuid}/refresh-name",
            headers=OTHER_HEADERS,
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_issue_certificate_requires_module_exam_if_exists(
    client: AsyncClient, scaffold, db_session: AsyncSession
):
    """If a module has modular exam questions, can_issue_certificate must reject
    issuance until a passing ExamAttempt exists for that module.
    """
    from app.models.base import new_uuid
    from app.models.progress import ExamAttempt
    from app.models.question import Option, Question

    course = scaffold["course"]
    user = scaffold["user"]

    # Get the module from DB
    from sqlalchemy import select

    from app.models.course import Module
    mod_result = await db_session.execute(
        select(Module).where(Module.course_id == course.id)
    )
    module = mod_result.scalars().first()
    assert module is not None

    # Create modular exam question
    question = Question(
        id=new_uuid(),
        module_id=module.id,
        enunciado="¿Examen modular?",
    )
    db_session.add(question)
    await db_session.flush()

    option = Option(
        id=new_uuid(),
        question_id=question.id,
        texto="Sí",
        is_correct=True,
        order_index=0,
    )
    db_session.add(option)
    await db_session.commit()

    # Attempt to issue. Since there's no approved module attempt, it must fail 422
    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/certificates/issue/{course.id}",
            headers=HEADERS,
        )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "course_incomplete"

    # Add passed attempt
    attempt = ExamAttempt(
        id=new_uuid(),
        user_id=user.id,
        module_id=module.id,
        score=100,
        passed=True,
        min_score_snapshot=70,
        answers={},
        created_at=datetime.now(UTC),
    )
    db_session.add(attempt)
    await db_session.commit()

    # Attempt again. It should now succeed (201)
    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post(
            f"/api/v1/certificates/issue/{course.id}",
            headers=HEADERS,
        )
    assert resp.status_code == 201
    assert resp.json()["course_title"] == "Cert Course Title"
