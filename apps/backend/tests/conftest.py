"""Test configuration: inject fake env vars before any app module is imported.

We set the minimum required env vars so pydantic-settings doesn't raise on startup.
All values are fake/safe — no real credentials.

IMPORTANT: app.db creates an async engine at module level with pool_size/max_overflow.
SQLite does not support these pool args. We patch create_async_engine before app.db
is imported to strip those kwargs when the URL is SQLite.
"""

import os

from sqlalchemy.ext.asyncio import create_async_engine as _real_create_async_engine

# Must be set BEFORE any app.* import (including conftest-level imports).
_TEST_ENV = {
    "DATABASE_URL": "sqlite+aiosqlite:///./test_auth.db",
    "STACK_PROJECT_ID": "test_project_id",
    "STACK_SECRET_SERVER_KEY": "test_secret_key",
    "STACK_JWKS_URL": "https://api.stack-auth.com/test/.well-known/jwks.json",
    "R2_ACCOUNT_ID": "test_account",
    "R2_ACCESS_KEY_ID": "test_key_id",
    "R2_SECRET_ACCESS_KEY": "test_secret",
    "R2_PUBLIC_BASE": "https://media.test.example",
    "MEDIA_JWT_SECRET": "test_media_secret_32chars_minimum_",
    "FRONTEND_URL": "http://localhost:5173",
    "RESEND_API_KEY": "",
    "CERTIFICATE_VERIFY_BASE_URL": "http://localhost:8000",
}

for key, value in _TEST_ENV.items():
    os.environ.setdefault(key, value)


def _sqlite_safe_engine(url: str, **kwargs):
    """Wrap create_async_engine to strip pool_size/max_overflow for SQLite URLs."""
    if str(url).startswith("sqlite"):
        kwargs.pop("pool_size", None)
        kwargs.pop("max_overflow", None)
    return _real_create_async_engine(url, **kwargs)


# Patch app.db's create_async_engine call at collection time.
# The patch target must be the name as used inside app.db (imported as create_async_engine).
import app.db  # noqa: E402 — must come after env vars are set

# Replace the module-level engine with a SQLite-compatible one.
app.db.engine = _sqlite_safe_engine(
    _TEST_ENV["DATABASE_URL"],
    pool_pre_ping=True,
)
app.db.AsyncSessionLocal = __import__("sqlalchemy.ext.asyncio", fromlist=["async_sessionmaker"]).async_sessionmaker(
    bind=app.db.engine,
    class_=__import__("sqlalchemy.ext.asyncio", fromlist=["AsyncSession"]).AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
