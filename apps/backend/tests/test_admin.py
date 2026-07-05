"""Admin router tests.

Test matrix (all 12 required cases):
1.  Estudiante NO puede acceder admin -> 403
2.  Instructor crea curso -> owner correcto (instructor_id = self)
3.  Instructor NO puede editar curso de otro instructor -> 403
4.  Admin puede editar cualquier curso
5.  DELETE curso con enrollments -> 409
6.  POST module con title <3 chars -> 422
7.  POST question con 2 opciones -> 422
8.  Reorder modules persiste order_index
9.  Audit log se escribe en POST course
10. Reports CSV streaming devuelve content correcto (enrollments + completions)
11. Stuck students filter funciona

SQLite via aiosqlite. verify_stack_token is monkeypatched per test.
db_session is the authoritative session for direct DB inspection/mutation.
The client fixture shares the same engine via dependency_override.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_URL = "sqlite+aiosqlite:///./test_admin.db"

FAKE_ADMIN_SUB = "neon_admin_001"
FAKE_INSTRUCTOR_SUB = "neon_instructor_001"
FAKE_INSTRUCTOR2_SUB = "neon_instructor_002"
FAKE_STUDENT_SUB = "neon_student_001"

ADMIN_HEADERS = {"Authorization": "Bearer admin-token"}
INSTRUCTOR_HEADERS = {"Authorization": "Bearer instructor-token"}
INSTRUCTOR2_HEADERS = {"Authorization": "Bearer instructor2-token"}
STUDENT_HEADERS = {"Authorization": "Bearer student-token"}


# ---------------------------------------------------------------------------
# Fixtures — engine shared between client and db_session
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def engine():
    # Import all models to register metadata
    import app.models.audit  # noqa: F401
    import app.models.certificate  # noqa: F401
    import app.models.course  # noqa: F401
    import app.models.progress  # noqa: F401
    import app.models.question  # noqa: F401
    import app.models.user  # noqa: F401
    from app.models.base import Base

    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def session_factory(engine):
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Direct DB session for test setup/inspection."""
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(engine, session_factory) -> AsyncGenerator[AsyncClient, None]:
    import app.db as _db_module
    from app.main import app
    from app.routers.auth import limiter

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[_db_module.get_db] = override_get_db
    limiter._storage.reset()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_claims(sub: str, email: str, name: str) -> Any:
    from app.security.neon_auth import StackAuthClaims
    return StackAuthClaims(sub=sub, email=email, name=name)


def _mock_verify_for(sub: str, email: str, name: str) -> AsyncMock:
    return AsyncMock(return_value=_make_claims(sub, email, name))


def _birth_date(age: int) -> str:
    today = date.today()
    return date(today.year - age, today.month, today.day).isoformat()


async def _sync_user(
    client: AsyncClient,
    sub: str,
    email: str,
    name: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    """Create user via /auth/sync endpoint."""
    with patch("app.routers.auth.verify_stack_token", _mock_verify_for(sub, email, name)):
        resp = await client.post(
            "/api/v1/auth/sync",
            json={"full_name": name, "birth_date": _birth_date(25)},
            headers=headers,
        )
    assert resp.status_code == 200, f"sync failed: {resp.text}"
    return resp.json()


async def _promote(db: AsyncSession, sub: str, role: str) -> None:
    """Elevate user role directly in DB (bypasses auth)."""
    from sqlalchemy import select

    from app.models.user import User

    result = await db.execute(select(User).where(User.neon_user_id == sub))
    user = result.scalar_one_or_none()
    if user:
        user.role = role
        await db.commit()


async def _get_user(db: AsyncSession, sub: str):  # type: ignore[return]
    from sqlalchemy import select

    from app.models.user import User

    result = await db.execute(select(User).where(User.neon_user_id == sub))
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Test 1: Estudiante NO puede acceder admin -> 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_student_cannot_access_admin(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_STUDENT_SUB, "student@test.com", "Student", STUDENT_HEADERS)

    with patch("app.deps.verify_stack_token", _mock_verify_for(FAKE_STUDENT_SUB, "student@test.com", "Student")):
        resp = await client.get("/api/v1/admin/courses", headers=STUDENT_HEADERS)

    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Test 2: Instructor crea curso -> owner correcto (instructor_id = self)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_instructor_creates_course_owns_it(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_INSTRUCTOR_SUB, "instructor@test.com", "Instructor", INSTRUCTOR_HEADERS)
    await _promote(db, FAKE_INSTRUCTOR_SUB, "instructor")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_INSTRUCTOR_SUB, "instructor@test.com", "Instructor"),
    ):
        resp = await client.post(
            "/api/v1/admin/courses",
            json={
                "title": "My Course Title",
                "short_desc": "Short description here",
                "age_min": 18,
                "age_max": 65,
                "slug": "my-course-title",
            },
            headers=INSTRUCTOR_HEADERS,
        )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "borrador"

    instructor = await _get_user(db, FAKE_INSTRUCTOR_SUB)
    assert data["instructor_id"] == str(instructor.id)


# ---------------------------------------------------------------------------
# Test 3: Instructor NO puede editar curso de otro instructor -> 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_instructor_cannot_edit_other_course(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_INSTRUCTOR_SUB, "instructor@test.com", "Instructor", INSTRUCTOR_HEADERS)
    await _promote(db, FAKE_INSTRUCTOR_SUB, "instructor")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_INSTRUCTOR_SUB, "instructor@test.com", "Instructor"),
    ):
        resp = await client.post(
            "/api/v1/admin/courses",
            json={
                "title": "Instructor One Course",
                "short_desc": "Belongs to instructor one",
                "slug": "instructor-one-course",
                "age_min": 18,
                "age_max": 65,
            },
            headers=INSTRUCTOR_HEADERS,
        )
    assert resp.status_code == 201
    course_id = resp.json()["id"]

    await _sync_user(client, FAKE_INSTRUCTOR2_SUB, "instructor2@test.com", "Instructor Two", INSTRUCTOR2_HEADERS)
    await _promote(db, FAKE_INSTRUCTOR2_SUB, "instructor")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_INSTRUCTOR2_SUB, "instructor2@test.com", "Instructor Two"),
    ):
        resp = await client.patch(
            f"/api/v1/admin/courses/{course_id}",
            json={"title": "Hijacked Title aaaaa"},
            headers=INSTRUCTOR2_HEADERS,
        )

    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Test 4: Admin puede editar cualquier curso
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_can_edit_any_course(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_INSTRUCTOR_SUB, "instructor@test.com", "Instructor", INSTRUCTOR_HEADERS)
    await _promote(db, FAKE_INSTRUCTOR_SUB, "instructor")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_INSTRUCTOR_SUB, "instructor@test.com", "Instructor"),
    ):
        resp = await client.post(
            "/api/v1/admin/courses",
            json={
                "title": "Instructor Course Edit",
                "short_desc": "Instructor owns this course",
                "slug": "instructor-course-edit",
                "age_min": 18,
                "age_max": 65,
            },
            headers=INSTRUCTOR_HEADERS,
        )
    assert resp.status_code == 201
    course_id = resp.json()["id"]

    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.patch(
            f"/api/v1/admin/courses/{course_id}",
            json={"title": "Admin Updated Title ab"},
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["title"] == "Admin Updated Title ab"


# ---------------------------------------------------------------------------
# Test 5: DELETE curso con enrollments -> 409
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_course_with_enrollments_returns_409(
    client: AsyncClient, db: AsyncSession
) -> None:
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.post(
            "/api/v1/admin/courses",
            json={
                "title": "Course To Delete Enroll",
                "short_desc": "Will have enrollment here",
                "slug": "course-to-delete-enroll",
                "age_min": 13,
                "age_max": 99,
            },
            headers=ADMIN_HEADERS,
        )
    assert resp.status_code == 201
    course_id = resp.json()["id"]

    # Inject enrollment directly via db session
    from app.models.progress import Enrollment

    admin = await _get_user(db, FAKE_ADMIN_SUB)
    enrollment = Enrollment(
        user_id=admin.id,
        course_id=uuid.UUID(course_id),
        started_at=datetime.now(UTC),
    )
    db.add(enrollment)
    await db.commit()

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.delete(
            f"/api/v1/admin/courses/{course_id}",
            params={"confirmation_title": "Course To Delete Enroll"},
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "has_enrollments"


# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_course_requires_exact_title_confirmation(
    client: AsyncClient, db: AsyncSession
) -> None:
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        create_resp = await client.post(
            "/api/v1/admin/courses",
            json={
                "title": "Danger Delete Course",
                "short_desc": "Course for delete confirmation",
                "slug": "danger-delete-course",
                "age_min": 13,
                "age_max": 99,
            },
            headers=ADMIN_HEADERS,
        )
        assert create_resp.status_code == 201
        course_id = create_resp.json()["id"]

        mismatch = await client.delete(
            f"/api/v1/admin/courses/{course_id}",
            params={"confirmation_title": "danger delete course"},
            headers=ADMIN_HEADERS,
        )
        deleted = await client.delete(
            f"/api/v1/admin/courses/{course_id}",
            params={"confirmation_title": "Danger Delete Course"},
            headers=ADMIN_HEADERS,
        )

    assert mismatch.status_code == 422, mismatch.text
    assert mismatch.json()["detail"]["code"] == "confirmation_mismatch"
    assert deleted.status_code == 204, deleted.text


# Test 6: POST module con title <3 chars -> 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_module_short_title_422(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.post(
            "/api/v1/admin/courses",
            json={
                "title": "Course For Module Test",
                "short_desc": "Testing module creation here",
                "slug": "course-for-module-test",
                "age_min": 13,
                "age_max": 99,
            },
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 201
        course_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/admin/courses/{course_id}/modules",
            json={"title": "AB"},
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 422, resp.text


# ---------------------------------------------------------------------------
# Test 7: POST question con 2 opciones -> 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_question_two_options_422(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    topic_id = uuid.uuid4()

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.post(
            f"/api/v1/admin/topics/{topic_id}/questions",
            json={
                "enunciado": "What is the capital city?",
                "options": [
                    {"texto": "Paris", "is_correct": True, "order_index": 0},
                    {"texto": "Berlin", "is_correct": False, "order_index": 1},
                ],
            },
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_replace_topic_questions_bulk_archives_old_questions(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    from sqlalchemy import select

    from app.models.base import new_uuid
    from app.models.course import Course, Module, Topic
    from app.models.question import Question

    course = Course(
        id=new_uuid(),
        slug="bulk-course",
        title="Bulk Course",
        short_desc="",
        long_desc="",
        status="publicado",
    )
    db.add(course)
    await db.flush()
    module = Module(id=new_uuid(), course_id=course.id, title="Bulk Module", description="")
    db.add(module)
    await db.flush()
    topic = Topic(id=new_uuid(), module_id=module.id, title="Bulk Topic", content_type="texto", has_exam=True)
    db.add(topic)
    await db.commit()

    first_payload = [
        {
            "enunciado": "Primera pregunta válida",
            "options": [
                {"texto": "A", "is_correct": True},
                {"texto": "B", "is_correct": False},
                {"texto": "C", "is_correct": False},
            ],
        },
        {
            "enunciado": "Segunda pregunta válida",
            "options": [
                {"texto": "A", "is_correct": False},
                {"texto": "B", "is_correct": True},
                {"texto": "C", "is_correct": False},
            ],
        },
    ]
    second_payload = [first_payload[1]]

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        first = await client.post(
            f"/api/v1/admin/topics/{topic.id}/questions/bulk",
            json=first_payload,
            headers=ADMIN_HEADERS,
        )
        second = await client.post(
            f"/api/v1/admin/topics/{topic.id}/questions/bulk",
            json=second_payload,
            headers=ADMIN_HEADERS,
        )

    assert first.status_code == 200, first.text
    assert [q["order_index"] for q in first.json()] == [0, 1]
    assert second.status_code == 200, second.text
    assert len(second.json()) == 1
    assert second.json()[0]["enunciado"] == "Segunda pregunta válida"

    await db.rollback()
    result = await db.execute(select(Question).where(Question.topic_id == topic.id))
    all_questions = list(result.scalars().all())
    assert sum(1 for q in all_questions if q.archived_at is None) == 1
    assert sum(1 for q in all_questions if q.archived_at is not None) == 2


# ---------------------------------------------------------------------------
# Test 8: Reorder modules persiste order_index
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reorder_modules_persists(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.post(
            "/api/v1/admin/courses",
            json={
                "title": "Reorder Course Title Test",
                "short_desc": "Course for reorder testing",
                "slug": "reorder-course-title-test",
                "age_min": 13,
                "age_max": 99,
            },
            headers=ADMIN_HEADERS,
        )
        course_id = resp.json()["id"]

        resp_a = await client.post(
            f"/api/v1/admin/courses/{course_id}/modules",
            json={"title": "Module Alpha"},
            headers=ADMIN_HEADERS,
        )
        resp_b = await client.post(
            f"/api/v1/admin/courses/{course_id}/modules",
            json={"title": "Module Beta"},
            headers=ADMIN_HEADERS,
        )
        mod_a_id = resp_a.json()["id"]
        mod_b_id = resp_b.json()["id"]

        resp = await client.post(
            "/api/v1/admin/modules/reorder",
            json={"course_id": course_id, "order": [mod_b_id, mod_a_id]},
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 200, resp.text
    items = resp.json()
    order_map = {item["id"]: item["order_index"] for item in items}
    assert order_map[mod_b_id] == 0
    assert order_map[mod_a_id] == 1


# ---------------------------------------------------------------------------
# Test 9: Audit log se escribe en POST course
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_log_written_on_course_create(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.post(
            "/api/v1/admin/courses",
            json={
                "title": "Audit Test Course Ok",
                "short_desc": "Testing audit log write path",
                "slug": "audit-test-course-ok",
                "age_min": 13,
                "age_max": 99,
            },
            headers=ADMIN_HEADERS,
        )
    assert resp.status_code == 201

    from sqlalchemy import select

    from app.models.audit import AdminAudit

    # Expire to pick up committed rows from the request
    await db.rollback()
    result = await db.execute(
        select(AdminAudit).where(
            AdminAudit.action == "create",
            AdminAudit.entity == "course",
        )
    )
    entries = list(result.scalars().all())
    assert len(entries) >= 1
    assert entries[0].entity == "course"
    assert "title" in entries[0].payload


# ---------------------------------------------------------------------------
# Test 10: Reports CSV streaming
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_report_csv_enrollments(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.get(
            "/api/v1/admin/reports/export?type=enrollments",
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 200, resp.text
    assert "text/csv" in resp.headers["content-type"]
    assert "enrollment_id" in resp.text
    assert "Content-Disposition" in resp.headers
    assert "enrollments-" in resp.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_report_csv_completions(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.get(
            "/api/v1/admin/reports/export?type=completions",
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 200
    assert "completed_at" in resp.text


# ---------------------------------------------------------------------------
# Test 11: Stuck students filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stuck_students_filter(client: AsyncClient, db: AsyncSession) -> None:
    """A student with 3 consecutive failed attempts on the same topic is is_stuck=True."""
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    await _sync_user(client, FAKE_STUDENT_SUB, "student@test.com", "Stuck Student", STUDENT_HEADERS)

    from app.models.progress import ExamAttempt

    student = await _get_user(db, FAKE_STUDENT_SUB)
    topic_id = uuid.uuid4()

    for _ in range(3):
        db.add(ExamAttempt(
            user_id=student.id,
            topic_id=topic_id,
            module_id=None,
            score=40,
            passed=False,
            min_score_snapshot=70,
            answers={},
            created_at=datetime.now(UTC),
        ))
    await db.commit()

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.get("/api/v1/admin/students", headers=ADMIN_HEADERS)

    assert resp.status_code == 200, resp.text
    data = resp.json()
    stuck = [s for s in data["items"] if s["is_stuck"]]
    assert len(stuck) >= 1
    assert stuck[0]["full_name"] == "Stuck Student"


@pytest.mark.asyncio
async def test_student_detail_exposes_progress_status_and_attempt_titles(client: AsyncClient, db: AsyncSession) -> None:
    await _sync_user(client, FAKE_ADMIN_SUB, "admin@test.com", "Admin User", ADMIN_HEADERS)
    await _promote(db, FAKE_ADMIN_SUB, "admin")

    from app.models.base import new_uuid
    from app.models.course import Course, Module, Topic
    from app.models.progress import Enrollment, ExamAttempt
    from app.models.user import User

    student = User(
        id=new_uuid(),
        neon_user_id="neon_detail_student",
        email="detail@student.test",
        full_name="Detail Student",
        birth_date=date(2000, 1, 1),
        role="estudiante",
        status="activo",
    )
    course = Course(
        id=new_uuid(),
        slug="detail-course",
        title="Detail Course",
        short_desc="",
        long_desc="",
        status="publicado",
    )
    db.add_all([student, course])
    await db.flush()
    module = Module(id=new_uuid(), course_id=course.id, title="Detail Module", description="")
    db.add(module)
    await db.flush()
    topic = Topic(id=new_uuid(), module_id=module.id, title="Detail Topic", content_type="texto", has_exam=True)
    db.add(topic)
    await db.flush()
    db.add(
        Enrollment(
            id=new_uuid(),
            user_id=student.id,
            course_id=course.id,
            started_at=datetime.now(UTC),
            progress_cached=45,
        )
    )
    db.add(
        ExamAttempt(
            id=new_uuid(),
            user_id=student.id,
            topic_id=topic.id,
            module_id=None,
            score=80,
            passed=True,
            min_score_snapshot=70,
            answers={},
            created_at=datetime.now(UTC),
        )
    )
    await db.commit()

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_ADMIN_SUB, "admin@test.com", "Admin User"),
    ):
        resp = await client.get(f"/api/v1/admin/students/{student.id}", headers=ADMIN_HEADERS)

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["enrollments"][0]["progress_cached"] == 45
    assert data["enrollments"][0]["progress_percentage"] == 45
    assert data["enrollments"][0]["status"] == "en_progreso"
    assert data["exam_attempts"][0]["topic_title"] == "Detail Topic"


@pytest.mark.asyncio
async def test_instructor_cannot_manage_nested_resources_from_other_course(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    await _sync_user(client, FAKE_INSTRUCTOR_SUB, "instructor@test.com", "Instructor", INSTRUCTOR_HEADERS)
    await _promote(db, FAKE_INSTRUCTOR_SUB, "instructor")
    await _sync_user(
        client,
        FAKE_INSTRUCTOR2_SUB,
        "instructor2@test.com",
        "Instructor Two",
        INSTRUCTOR2_HEADERS,
    )
    await _promote(db, FAKE_INSTRUCTOR2_SUB, "instructor")

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_INSTRUCTOR_SUB, "instructor@test.com", "Instructor"),
    ):
        course_resp = await client.post(
            "/api/v1/admin/courses",
            json={
                "title": "Nested Owner Course",
                "short_desc": "Owned by instructor one",
                "slug": "nested-owner-course",
                "age_min": 13,
                "age_max": 99,
            },
            headers=INSTRUCTOR_HEADERS,
        )
        course_id = course_resp.json()["id"]
        module_resp = await client.post(
            f"/api/v1/admin/courses/{course_id}/modules",
            json={"title": "Owner Module"},
            headers=INSTRUCTOR_HEADERS,
        )
        module_id = module_resp.json()["id"]
        topic_resp = await client.post(
            f"/api/v1/admin/modules/{module_id}/topics",
            json={
                "title": "Owner Topic",
                "content_type": "texto",
                "content_body": "Contenido",
                "has_exam": True,
                "exam_min_score": 70,
            },
            headers=INSTRUCTOR_HEADERS,
        )
        topic_id = topic_resp.json()["id"]
        question_resp = await client.post(
            f"/api/v1/admin/topics/{topic_id}/questions",
            json={
                "enunciado": "Pregunta válida de propietario?",
                "options": [
                    {"texto": "Uno", "is_correct": True, "order_index": 0},
                    {"texto": "Dos", "is_correct": False, "order_index": 1},
                    {"texto": "Tres", "is_correct": False, "order_index": 2},
                    {"texto": "Cuatro", "is_correct": False, "order_index": 3},
                ],
            },
            headers=INSTRUCTOR_HEADERS,
        )
        question_id = question_resp.json()["id"]
        option_id = question_resp.json()["options"][0]["id"]

    with patch(
        "app.deps.verify_stack_token",
        _mock_verify_for(FAKE_INSTRUCTOR2_SUB, "instructor2@test.com", "Instructor Two"),
    ):
        attempts = [
            await client.post(
                f"/api/v1/admin/courses/{course_id}/modules",
                json={"title": "Foreign Module"},
                headers=INSTRUCTOR2_HEADERS,
            ),
            await client.patch(
                f"/api/v1/admin/modules/{module_id}",
                json={"title": "Hijacked Module"},
                headers=INSTRUCTOR2_HEADERS,
            ),
            await client.post(
                "/api/v1/admin/modules/reorder",
                json={"course_id": course_id, "order": [module_id]},
                headers=INSTRUCTOR2_HEADERS,
            ),
            await client.post(
                f"/api/v1/admin/modules/{module_id}/topics",
                json={"title": "Foreign Topic", "content_type": "texto"},
                headers=INSTRUCTOR2_HEADERS,
            ),
            await client.patch(
                f"/api/v1/admin/topics/{topic_id}",
                json={"title": "Hijacked Topic"},
                headers=INSTRUCTOR2_HEADERS,
            ),
            await client.post(
                "/api/v1/admin/topics/reorder",
                json={"module_id": module_id, "order": [topic_id]},
                headers=INSTRUCTOR2_HEADERS,
            ),
            await client.post(
                f"/api/v1/admin/topics/{topic_id}/questions",
                json={
                    "enunciado": "Pregunta invasora?",
                    "options": [
                        {"texto": "Uno", "is_correct": True},
                        {"texto": "Dos", "is_correct": False},
                        {"texto": "Tres", "is_correct": False},
                        {"texto": "Cuatro", "is_correct": False},
                    ],
                },
                headers=INSTRUCTOR2_HEADERS,
            ),
            await client.patch(
                f"/api/v1/admin/questions/{question_id}",
                json={"enunciado": "Pregunta secuestrada?"},
                headers=INSTRUCTOR2_HEADERS,
            ),
            await client.patch(
                f"/api/v1/admin/options/{option_id}",
                json={"texto": "Opción secuestrada"},
                headers=INSTRUCTOR2_HEADERS,
            ),
        ]

    assert all(resp.status_code == 403 for resp in attempts), [resp.text for resp in attempts]
