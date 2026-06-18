import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'instructor', 'estudiante')", name="ck_users_role"),
        CheckConstraint("status IN ('nuevo', 'activo', 'completado', 'atorado')", name="ck_users_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    neon_user_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="estudiante")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="nuevo")

    courses: Mapped[list["Course"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Course", back_populates="instructor", foreign_keys="Course.instructor_id"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Enrollment", back_populates="user"
    )
    topic_progress: Mapped[list["TopicProgress"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "TopicProgress", back_populates="user"
    )
    exam_attempts: Mapped[list["ExamAttempt"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "ExamAttempt", back_populates="user"
    )
    certificates: Mapped[list["Certificate"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Certificate", back_populates="user"
    )
    audit_entries: Mapped[list["AdminAudit"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "AdminAudit", back_populates="actor"
    )
