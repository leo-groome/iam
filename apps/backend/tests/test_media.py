from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_URL = "sqlite+aiosqlite:///./test_media.db"

FAKE_SUB_ADMIN = "neon_media_admin_001"
FAKE_SUB_INSTRUCTOR = "neon_media_instructor_001"
FAKE_SUB_STUDENT = "neon_media_student_001"
HEADERS = {"Authorization": "Bearer fake-token"}


def _make_claims(sub: str = FAKE_SUB_ADMIN, email: str = "admin@example.com", name: str = "Admin"):
    from app.security.neon_auth import StackAuthClaims

    return StackAuthClaims(sub=sub, email=email, name=name)


def _mock_verify(sub: str = FAKE_SUB_ADMIN, email: str = "admin@example.com", name: str = "Admin"):
    return AsyncMock(return_value=_make_claims(sub=sub, email=email, name=name))


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


@pytest_asyncio.fixture
async def scaffold(db_session: AsyncSession):
    from app.models.base import new_uuid
    from app.models.course import Course, Module, Topic
    from app.models.progress import Enrollment
    from app.models.user import User

    admin = User(
        id=new_uuid(),
        neon_user_id=FAKE_SUB_ADMIN,
        email="admin@example.com",
        full_name="Admin User",
        birth_date=_birth_date_age(30),
        role="admin",
        status="activo",
    )
    instructor = User(
        id=new_uuid(),
        neon_user_id=FAKE_SUB_INSTRUCTOR,
        email="instructor@example.com",
        full_name="Instructor User",
        birth_date=_birth_date_age(28),
        role="instructor",
        status="activo",
    )
    student = User(
        id=new_uuid(),
        neon_user_id=FAKE_SUB_STUDENT,
        email="student@example.com",
        full_name="Student User",
        birth_date=_birth_date_age(20),
        role="estudiante",
        status="activo",
    )
    db_session.add_all([admin, instructor, student])

    course = Course(
        id=new_uuid(),
        slug="media-course",
        title="Media Course",
        short_desc="",
        long_desc="",
        order_index=0,
        status="publicado",
    )
    db_session.add(course)
    await db_session.flush()

    mod1 = Module(id=new_uuid(), course_id=course.id, title="Module 1", order_index=0)
    db_session.add(mod1)
    await db_session.flush()

    topic_with_media = Topic(
        id=new_uuid(),
        module_id=mod1.id,
        title="Video Topic",
        content_type="video",
        media_key="video/abc123/lecture.mp4",
        has_exam=False,
        exam_min_score=70,
        order_index=0,
    )
    topic_no_media = Topic(
        id=new_uuid(),
        module_id=mod1.id,
        title="Text Topic",
        content_type="texto",
        media_key=None,
        has_exam=False,
        exam_min_score=70,
        order_index=1,
    )
    db_session.add_all([topic_with_media, topic_no_media])

    enrollment = Enrollment(
        id=new_uuid(),
        user_id=student.id,
        course_id=course.id,
        started_at=datetime.now(UTC),
    )
    db_session.add(enrollment)

    await db_session.commit()
    await db_session.refresh(topic_with_media)
    await db_session.refresh(topic_no_media)

    return {
        "admin": admin,
        "instructor": instructor,
        "student": student,
        "course": course,
        "mod1": mod1,
        "topic_with_media": topic_with_media,
        "topic_no_media": topic_no_media,
    }


# ── /upload-url ───────────────────────────────────────────────────────────────


def _mock_r2_upload(put_url: str = "https://r2.example.com/presigned-put"):
    """Patch both build_key and generate_upload_url to avoid real R2 calls."""
    mock_build = AsyncMock(return_value="video/test-uuid/lecture.mp4")
    mock_upload = AsyncMock(return_value=put_url)
    return mock_build, mock_upload


@pytest.mark.asyncio
async def test_upload_url_admin_success(client: AsyncClient, scaffold):
    mock_build, mock_upload = _mock_r2_upload()
    with (
        patch("app.deps.verify_stack_token", _mock_verify(sub=FAKE_SUB_ADMIN)),
        patch("app.routers.media.build_key", mock_build),
        patch("app.routers.media.generate_upload_url", mock_upload),
    ):
        resp = await client.post(
            "/api/v1/media/upload-url",
            json={"filename": "lecture.mp4", "content_type": "video/mp4", "scope": "video"},
            headers=HEADERS,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "put_url" in data
    assert "key" in data
    assert data["expires_in"] == 600


@pytest.mark.asyncio
async def test_upload_url_instructor_success(client: AsyncClient, scaffold):
    mock_build, mock_upload = _mock_r2_upload()
    with (
        patch(
            "app.deps.verify_stack_token",
            _mock_verify(
                sub=FAKE_SUB_INSTRUCTOR,
                email="instructor@example.com",
                name="Instructor User",
            ),
        ),
        patch("app.routers.media.build_key", mock_build),
        patch("app.routers.media.generate_upload_url", mock_upload),
    ):
        resp = await client.post(
            "/api/v1/media/upload-url",
            json={"filename": "slides.pdf", "content_type": "application/pdf", "scope": "pdf"},
            headers=HEADERS,
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_upload_url_student_forbidden(client: AsyncClient, scaffold):
    with patch(
        "app.deps.verify_stack_token",
        _mock_verify(sub=FAKE_SUB_STUDENT, email="student@example.com", name="Student User"),
    ):
        resp = await client.post(
            "/api/v1/media/upload-url",
            json={"filename": "lecture.mp4", "content_type": "video/mp4", "scope": "video"},
            headers=HEADERS,
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_upload_url_invalid_content_type_for_scope(client: AsyncClient, scaffold):
    mock_build, mock_upload = _mock_r2_upload()
    with (
        patch("app.deps.verify_stack_token", _mock_verify(sub=FAKE_SUB_ADMIN)),
        patch("app.routers.media.build_key", mock_build),
        patch("app.routers.media.generate_upload_url", mock_upload),
    ):
        # Sending a PDF content-type for a video scope
        resp = await client.post(
            "/api/v1/media/upload-url",
            json={"filename": "lecture.pdf", "content_type": "application/pdf", "scope": "video"},
            headers=HEADERS,
        )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "invalid_content_type"


@pytest.mark.asyncio
async def test_upload_url_image_wrong_type_for_pdf_scope(client: AsyncClient, scaffold):
    mock_build, mock_upload = _mock_r2_upload()
    with (
        patch("app.deps.verify_stack_token", _mock_verify(sub=FAKE_SUB_ADMIN)),
        patch("app.routers.media.build_key", mock_build),
        patch("app.routers.media.generate_upload_url", mock_upload),
    ):
        resp = await client.post(
            "/api/v1/media/upload-url",
            json={"filename": "cover.jpg", "content_type": "image/jpeg", "scope": "pdf"},
            headers=HEADERS,
        )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "invalid_content_type"


# ── /play-token ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_play_token_topic_locked_returns_403(client: AsyncClient, scaffold):
    topic = scaffold["topic_with_media"]
    with (
        patch(
            "app.deps.verify_stack_token",
            _mock_verify(
                sub=FAKE_SUB_STUDENT,
                email="student@example.com",
                name="Student User",
            ),
        ),
        patch("app.routers.media.compute_topic_state", AsyncMock(return_value="bloqueado")),
    ):
        resp = await client.post(
            "/api/v1/media/play-token",
            json={"topic_id": str(topic.id)},
            headers=HEADERS,
        )
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "topic_locked"


@pytest.mark.asyncio
async def test_play_token_requires_enrollment(client: AsyncClient, scaffold):
    topic = scaffold["topic_with_media"]
    with (
        patch(
            "app.deps.verify_stack_token",
            _mock_verify(
                sub=FAKE_SUB_INSTRUCTOR,
                email="instructor@example.com",
                name="Instructor User",
            ),
        ),
        patch("app.routers.media.compute_topic_state", AsyncMock(return_value="disponible")),
    ):
        resp = await client.post(
            "/api/v1/media/play-token",
            json={"topic_id": str(topic.id)},
            headers=HEADERS,
        )
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "not_enrolled"


@pytest.mark.asyncio
async def test_play_token_topic_no_media_key_returns_422(client: AsyncClient, scaffold):
    topic_no_media = scaffold["topic_no_media"]
    with (
        patch(
            "app.deps.verify_stack_token",
            _mock_verify(
                sub=FAKE_SUB_STUDENT,
                email="student@example.com",
                name="Student User",
            ),
        ),
        patch("app.routers.media.compute_topic_state", AsyncMock(return_value="disponible")),
    ):
        resp = await client.post(
            "/api/v1/media/play-token",
            json={"topic_id": str(topic_no_media.id)},
            headers=HEADERS,
        )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "no_media_key"


@pytest.mark.asyncio
async def test_play_token_returns_valid_jwt(client: AsyncClient, scaffold):
    from app.security.media_jwt import verify_play_token

    topic = scaffold["topic_with_media"]
    student = scaffold["student"]

    with (
        patch(
            "app.deps.verify_stack_token",
            _mock_verify(
                sub=FAKE_SUB_STUDENT,
                email="student@example.com",
                name="Student User",
            ),
        ),
        patch("app.routers.media.compute_topic_state", AsyncMock(return_value="disponible")),
    ):
        resp = await client.post(
            "/api/v1/media/play-token",
            json={"topic_id": str(topic.id)},
            headers=HEADERS,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert "media_url" in data
    assert data["expires_in"] == 900
    assert topic.media_key in data["media_url"]

    # Decode and verify the JWT locally
    claims = verify_play_token(data["token"])
    assert claims["key"] == topic.media_key
    assert claims["sub"] == str(student.id)
    assert claims["aud"] == "r2-worker"


@pytest.mark.asyncio
async def test_play_token_topic_not_found_returns_404(client: AsyncClient, scaffold):
    import uuid

    with (
        patch(
            "app.deps.verify_stack_token",
            _mock_verify(
                sub=FAKE_SUB_STUDENT,
                email="student@example.com",
                name="Student User",
            ),
        ),
    ):
        resp = await client.post(
            "/api/v1/media/play-token",
            json={"topic_id": str(uuid.uuid4())},
            headers=HEADERS,
        )
    assert resp.status_code == 404
