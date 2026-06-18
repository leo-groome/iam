"""initial schema

Revision ID: c92e06fd8e9f
Revises:
Create Date: 2026-06-18 08:01:11.853766

NOTE: email uses VARCHAR(320) lowercased in app code (not CITEXT) to avoid requiring
the citext extension. To enable CITEXT on Neon run: CREATE EXTENSION IF NOT EXISTS citext;
then change the column type to CITEXT for case-insensitive uniqueness enforcement at DB level.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c92e06fd8e9f"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("neon_user_id", sa.Text(), unique=True, nullable=False),
        sa.Column("email", sa.String(320), unique=True, nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="estudiante"),
        sa.Column("status", sa.String(20), nullable=False, server_default="nuevo"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('admin', 'instructor', 'estudiante')", name="ck_users_role"),
        sa.CheckConstraint("status IN ('nuevo', 'activo', 'completado', 'atorado')", name="ck_users_status"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(120), unique=True, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("short_desc", sa.String(500), nullable=False, server_default=""),
        sa.Column("long_desc", sa.Text(), nullable=False, server_default=""),
        sa.Column("cover_key", sa.Text(), nullable=True),
        sa.Column("age_min", sa.Integer(), nullable=True),
        sa.Column("age_max", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="borrador"),
        sa.Column("instructor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('borrador', 'publicado', 'archivado')", name="ck_courses_status"),
    )
    op.create_index("ix_courses_slug", "courses", ["slug"])
    op.create_index("ix_courses_status_order", "courses", ["status", "order_index"])

    op.create_table(
        "modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_modules_course_order", "modules", ["course_id", "order_index"])

    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content_type", sa.String(20), nullable=False),
        sa.Column("content_body", sa.Text(), nullable=True),
        sa.Column("media_key", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("has_exam", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("exam_min_score", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("content_type IN ('video', 'pdf', 'imagen', 'texto')", name="ck_topics_content_type"),
        sa.CheckConstraint("exam_min_score >= 50 AND exam_min_score <= 100", name="ck_topics_min_score"),
    )
    op.create_index("ix_topics_module_order", "topics", ["module_id", "order_index"])

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=True),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=True),
        sa.Column("enunciado", sa.Text(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("(topic_id IS NULL) <> (module_id IS NULL)", name="ck_questions_xor_scope"),
    )
    op.create_index("ix_questions_topic", "questions", ["topic_id"])
    op.create_index("ix_questions_module", "questions", ["module_id"])

    op.create_table(
        "options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_options_question", "options", ["question_id"])

    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("progress_cached", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "course_id", name="uq_enrollments_user_course"),
    )
    op.create_index("ix_enrollments_user", "enrollments", ["user_id"])
    op.create_index("ix_enrollments_course", "enrollments", ["course_id"])

    op.create_table(
        "topic_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(30), nullable=False, server_default="bloqueado"),
        sa.Column("video_last_pos_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("video_max_seen_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pdf_last_page", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pdf_total_pages", sa.Integer(), nullable=True),
        sa.Column("content_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "state IN ('bloqueado', 'disponible', 'contenido_visto', 'aprobado', 'en_repaso')",
            name="ck_topic_progress_state",
        ),
        sa.UniqueConstraint("user_id", "topic_id", name="uq_topic_progress_user_topic"),
    )
    op.create_index("ix_topic_progress_user_topic", "topic_progress", ["user_id", "topic_id"])

    op.create_table(
        "exam_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=True),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("min_score_snapshot", sa.Integer(), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("(topic_id IS NULL) <> (module_id IS NULL)", name="ck_exam_attempts_xor_scope"),
    )
    op.create_index("ix_exam_attempts_user_topic", "exam_attempts", ["user_id", "topic_id"])
    op.create_index("ix_exam_attempts_user_module", "exam_attempts", ["user_id", "module_id"])

    op.create_table(
        "certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("public_uuid", postgresql.UUID(as_uuid=True), unique=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("student_name_snapshot", sa.Text(), nullable=False),
        sa.Column("course_title_snapshot", sa.Text(), nullable=False),
        sa.UniqueConstraint("user_id", "course_id", name="uq_certificates_user_course"),
    )
    op.create_index("ix_certificates_public_uuid", "certificates", ["public_uuid"], unique=True)

    op.create_table(
        "admin_audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_admin_audit_actor", "admin_audit", ["actor_id"])
    op.create_index("ix_admin_audit_entity", "admin_audit", ["entity", "entity_id"])
    op.create_index("ix_admin_audit_payload_gin", "admin_audit", ["payload"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_table("admin_audit")
    op.drop_table("certificates")
    op.drop_table("exam_attempts")
    op.drop_table("topic_progress")
    op.drop_table("enrollments")
    op.drop_table("options")
    op.drop_table("questions")
    op.drop_table("topics")
    op.drop_table("modules")
    op.drop_table("courses")
    op.drop_table("users")
