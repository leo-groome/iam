"""Auth endpoint tests.

Uses SQLite in-memory (aiosqlite) so tests run without a real Neon connection.
verify_stack_token is monkeypatched — no network calls in tests.

Test matrix:
- sync: new valid user -> 200, user created in DB
- sync: age < 13 -> 422 under_age
- sync: age > 120 -> 422 invalid_age
- /me: no token -> 422 (Header required) or 401
- /me: valid token but no DB user -> 409 setup_required
- /me: valid token + DB user -> 200 UserPublic
- /me/logout: valid user -> 204

NOTE: conftest.py sets env vars before any app import. app.db creates its engine
at module level with pool_size which SQLite rejects, so we patch get_db directly.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Use a file-based SQLite DB per test run to avoid StaticPool issues with aiosqlite
TEST_DB_URL = "sqlite+aiosqlite:///./test_auth.db"


@pytest_asyncio.fixture(scope="function")
async def engine():
    from app.models.user import User  # registers table on Base.metadata

    eng = create_async_engine(TEST_DB_URL, echo=False)
    users_table = User.__table__
    async with eng.begin() as conn:
        await conn.run_sync(users_table.create, checkfirst=True)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(users_table.drop, checkfirst=True)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(engine) -> AsyncGenerator[AsyncClient, None]:
    """Test client with DB override pointing to in-memory SQLite.

    Also resets the slowapi rate limiter between tests so 5/minute limit
    doesn't accumulate across the test suite.
    """
    import app.db as _db_module
    from app.main import app
    from app.routers.auth import limiter

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    app.dependency_overrides[_db_module.get_db] = override_get_db

    # Reset in-memory rate limit storage so each test starts with a clean counter.
    limiter._storage.reset()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_SUB = "neon_test_user_001"
FAKE_EMAIL = "test@example.com"
FAKE_NAME = "Test User"

VALID_CLAIMS = {
    "sub": FAKE_SUB,
    "email": FAKE_EMAIL,
    "name": FAKE_NAME,
}


def _make_claims(**overrides: Any):
    from app.security.neon_auth import StackAuthClaims
    data = {**VALID_CLAIMS, **overrides}
    return StackAuthClaims(**data)


def _mock_verify(claims_override: dict | None = None):
    """Return an async mock for verify_stack_token returning StackAuthClaims."""
    claims = _make_claims(**(claims_override or {}))
    return AsyncMock(return_value=claims)


HEADERS = {"Authorization": "Bearer fake.jwt.token"}

# Age helpers
def _birth_date_age(age: int) -> str:
    today = date.today()
    return date(today.year - age, today.month, today.day).isoformat()


# ---------------------------------------------------------------------------
# Tests: POST /api/v1/auth/sync
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_new_valid_user(client: AsyncClient) -> None:
    """New user with valid age is created; role forced to 'estudiante'."""
    with patch("app.routers.auth.verify_stack_token", _mock_verify()):
        resp = await client.post(
            "/api/v1/auth/sync",
            json={"full_name": "Test User", "birth_date": _birth_date_age(20)},
            headers=HEADERS,
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == FAKE_EMAIL
    assert data["full_name"] == "Test User"
    assert data["role"] == "estudiante"
    assert data["status"] == "nuevo"
    assert "id" in data


@pytest.mark.asyncio
async def test_sync_lowercases_email_from_claims(client: AsyncClient) -> None:
    with patch(
        "app.routers.auth.verify_stack_token",
        _mock_verify({"email": "TEST@Example.COM"}),
    ):
        resp = await client.post(
            "/api/v1/auth/sync",
            json={"full_name": "Test User", "birth_date": _birth_date_age(20)},
            headers=HEADERS,
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_sync_under_age(client: AsyncClient) -> None:
    """User aged 12 must be rejected with 422 under_age."""
    with patch("app.routers.auth.verify_stack_token", _mock_verify()):
        resp = await client.post(
            "/api/v1/auth/sync",
            json={"full_name": "Young User", "birth_date": _birth_date_age(12)},
            headers=HEADERS,
        )

    assert resp.status_code == 422, resp.text
    detail = resp.json()["detail"]
    assert detail["code"] == "under_age"


@pytest.mark.asyncio
async def test_sync_invalid_age_over_120(client: AsyncClient) -> None:
    """User aged 121 must be rejected with 422 invalid_age."""
    with patch("app.routers.auth.verify_stack_token", _mock_verify()):
        resp = await client.post(
            "/api/v1/auth/sync",
            json={"full_name": "Ancient User", "birth_date": _birth_date_age(121)},
            headers=HEADERS,
        )

    assert resp.status_code == 422, resp.text
    detail = resp.json()["detail"]
    assert detail["code"] == "invalid_age"


@pytest.mark.asyncio
async def test_sync_exactly_13(client: AsyncClient) -> None:
    """User aged exactly 13 must be accepted (boundary)."""
    with patch("app.routers.auth.verify_stack_token", _mock_verify()):
        resp = await client.post(
            "/api/v1/auth/sync",
            json={"full_name": "Teen User", "birth_date": _birth_date_age(13)},
            headers=HEADERS,
        )

    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_sync_idempotent_update(client: AsyncClient) -> None:
    """Calling sync twice updates name but never changes role."""
    with patch("app.routers.auth.verify_stack_token", _mock_verify()):
        await client.post(
            "/api/v1/auth/sync",
            json={"full_name": "Original Name", "birth_date": _birth_date_age(25)},
            headers=HEADERS,
        )
        resp = await client.post(
            "/api/v1/auth/sync",
            json={"full_name": "Updated Name", "birth_date": _birth_date_age(25)},
            headers=HEADERS,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Updated Name"
    assert data["role"] == "estudiante"  # role must not change


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/auth/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient) -> None:
    """Missing Authorization header -> 422 (required Header) or 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 422), resp.text


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient) -> None:
    """Malformed/invalid JWT -> 401."""
    import jwt as _jwt

    with patch(
        "app.deps.verify_stack_token",
        AsyncMock(side_effect=_jwt.InvalidTokenError("bad token")),
    ):
        resp = await client.get("/api/v1/auth/me", headers=HEADERS)

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_valid_token_no_db_user(client: AsyncClient) -> None:
    """Valid JWT but no DB user row -> 409 setup_required."""
    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.get("/api/v1/auth/me", headers=HEADERS)

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "setup_required"


@pytest.mark.asyncio
async def test_me_valid_user(client: AsyncClient) -> None:
    """Valid JWT + DB user -> 200 UserPublic."""
    # First create the user via sync
    with patch("app.routers.auth.verify_stack_token", _mock_verify()):
        await client.post(
            "/api/v1/auth/sync",
            json={"full_name": "Valid User", "birth_date": _birth_date_age(25)},
            headers=HEADERS,
        )

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.get("/api/v1/auth/me", headers=HEADERS)

    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == FAKE_EMAIL
    assert data["role"] == "estudiante"


@pytest.mark.asyncio
async def test_me_alias_valid_user(client: AsyncClient) -> None:
    with patch("app.routers.auth.verify_stack_token", _mock_verify()):
        await client.post(
            "/api/v1/auth/sync",
            json={"full_name": "Alias User", "birth_date": _birth_date_age(25)},
            headers=HEADERS,
        )

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.get("/api/v1/me", headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json()["email"] == FAKE_EMAIL


@pytest.mark.asyncio
async def test_logout(client: AsyncClient) -> None:
    """Logout endpoint is stateless; always 204 for authenticated user."""
    with patch("app.routers.auth.verify_stack_token", _mock_verify()):
        await client.post(
            "/api/v1/auth/sync",
            json={"full_name": "Logout User", "birth_date": _birth_date_age(25)},
            headers=HEADERS,
        )

    with patch("app.deps.verify_stack_token", _mock_verify()):
        resp = await client.post("/api/v1/auth/me/logout", headers=HEADERS)

    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Tests: role enforcement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_cannot_set_role(client: AsyncClient) -> None:
    """Client cannot inject role via request body (field not in schema)."""
    with patch("app.routers.auth.verify_stack_token", _mock_verify()):
        resp = await client.post(
            "/api/v1/auth/sync",
            # role field is not in SyncRequest; Pydantic ignores it
            json={"full_name": "Hacker User", "birth_date": _birth_date_age(20), "role": "admin"},
            headers=HEADERS,
        )

    assert resp.status_code == 200
    assert resp.json()["role"] == "estudiante"  # must NOT be 'admin'
