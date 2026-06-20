from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_URL = "sqlite+aiosqlite:///./test_catalog.db"

FAKE_SUB = "neon_catalog_user_001"
FAKE_EMAIL = "catalog@example.com"
FAKE_NAME = "Catalog User"
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


@pytest_asyncio.fixture
async def user_25(db_session: AsyncSession):
    from app.models.base import new_uuid
    from app.models.user import User

    u = User(
        id=new_uuid(),
        neon_user_id=FAKE_SUB,
        email=FAKE_EMAIL,
        full_name=FAKE_NAME,
        birth_date=_birth_date_age(25),
        role="estudiante",
        status="activo",
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest_asyncio.fixture
async def user_10(db_session: AsyncSession):
    from app.models.base import new_uuid
    from app.models.user import User

    sub = "neon_young_001"
    u = User(
        id=new_uuid(),
        neon_user_id=sub,
        email="young@example.com",
        full_name="Young User",
        birth_date=_birth_date_age(10),
        role="estudiante",
        status="activo",
    )
    db_session.add(u)
    await db_session.commit()
    return u


@pytest_asyncio.fixture
async def course_adult(db_session: AsyncSession):
    from app.models.base import new_uuid
    from app.models.course import Course

    c = Course(
        id=new_uuid(),
        slug="adult-course",
        title="Adult Course",
        short_desc="For adults",
        long_desc="",
        age_min=18,
        age_max=None,
        order_index=0,
        status="publicado",
    )
    db_session.add(c)
    await db_session.commit()
    return c


@pytest_asyncio.fixture
async def course_open(db_session: AsyncSession):
    from app.models.base import new_uuid
    from app.models.course import Course

    c = Course(
        id=new_uuid(),
        slug="open-course",
        title="Open Course",
        short_desc="For all ages",
        long_desc="",
        age_min=None,
        age_max=None,
        order_index=1,
        status="publicado",
    )
    db_session.add(c)
    await db_session.commit()
    return c


# ─── R-CAT-01: age filter ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_courses_age_filter_excludes_underage(
    client: AsyncClient, user_10, course_adult, course_open
):
    young_claims = _make_claims(sub=user_10.neon_user_id, email=user_10.email, name=user_10.full_name)
    with patch("app.deps.verify_stack_token", AsyncMock(return_value=young_claims)):
        resp = await client.get("/api/v1/courses", headers=HEADERS)

    assert resp.status_code == 200
    slugs = [c["slug"] for c in resp.json()["items"]]
    assert "adult-course" not in slugs
    assert "open-course" in slugs


@pytest.mark.asyncio
async def test_list_courses_age_filter_includes_eligible(
    client: AsyncClient, user_25, course_adult, course_open
):
    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.get("/api/v1/courses", headers=HEADERS)

    assert resp.status_code == 200
    slugs = [c["slug"] for c in resp.json()["items"]]
    assert "adult-course" in slugs
    assert "open-course" in slugs


@pytest.mark.asyncio
async def test_list_courses_archived_visible_if_enrolled(
    client: AsyncClient, db_session: AsyncSession, user_25, course_adult
):
    from app.models.base import new_uuid
    from app.models.course import Course
    from app.models.progress import Enrollment

    archived = Course(
        id=new_uuid(),
        slug="archived-course",
        title="Archived",
        short_desc="",
        long_desc="",
        order_index=99,
        status="archivado",
    )
    db_session.add(archived)
    await db_session.flush()

    enrollment = Enrollment(
        id=new_uuid(),
        user_id=user_25.id,
        course_id=archived.id,
        started_at=datetime.now(UTC),
    )
    db_session.add(enrollment)
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.get("/api/v1/courses", headers=HEADERS)

    assert resp.status_code == 200
    slugs = [c["slug"] for c in resp.json()["items"]]
    assert "archived-course" in slugs


# ─── Enroll: idempotent ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_enroll_idempotent(client: AsyncClient, user_25, course_open):
    with patch("app.deps.verify_stack_token", _mock_verify()):
        r1 = await client.post(f"/api/v1/courses/{course_open.slug}/enroll", headers=HEADERS)
        r2 = await client.post(f"/api/v1/courses/{course_open.slug}/enroll", headers=HEADERS)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


@pytest.mark.asyncio
async def test_enroll_age_restricted_fails(
    client: AsyncClient, user_10, course_adult
):
    young_claims = _make_claims(sub=user_10.neon_user_id, email=user_10.email, name=user_10.full_name)
    with patch("app.deps.verify_stack_token", AsyncMock(return_value=young_claims)):
        resp = await client.post(f"/api/v1/courses/{course_adult.slug}/enroll", headers=HEADERS)

    assert resp.status_code == 403


# ─── Cursor pagination ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_courses_cursor_pagination(
    client: AsyncClient, db_session: AsyncSession, user_25
):
    from app.models.base import new_uuid
    from app.models.course import Course

    for i in range(15):
        c = Course(
            id=new_uuid(),
            slug=f"pag-course-{i}",
            title=f"Pag Course {i}",
            short_desc="",
            long_desc="",
            order_index=i,
            status="publicado",
        )
        db_session.add(c)
    await db_session.commit()

    with patch("app.deps.verify_stack_token", _mock_verify()):
        r1 = await client.get("/api/v1/courses?limit=5", headers=HEADERS)

    assert r1.status_code == 200
    data = r1.json()
    assert len(data["items"]) == 5
    assert data["next_cursor"] is not None

    cursor = data["next_cursor"]
    with patch("app.deps.verify_stack_token", _mock_verify()):
        r2 = await client.get(f"/api/v1/courses?limit=5&cursor={cursor}", headers=HEADERS)

    assert r2.status_code == 200
    data2 = r2.json()
    assert len(data2["items"]) == 5
    slugs1 = {c["slug"] for c in data["items"]}
    slugs2 = {c["slug"] for c in data2["items"]}
    assert slugs1.isdisjoint(slugs2)
