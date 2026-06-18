import uuid as uuid_module

from sqlalchemy import DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_certificates_user_course"),
        Index("ix_certificates_public_uuid", "public_uuid", unique=True),
    )

    id: Mapped[uuid_module.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    public_uuid: Mapped[uuid_module.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=new_uuid
    )
    user_id: Mapped[uuid_module.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[uuid_module.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    issued_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    student_name_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    course_title_snapshot: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="certificates")  # type: ignore[name-defined]  # noqa: F821
    course: Mapped["Course"] = relationship("Course", back_populates="certificates")  # type: ignore[name-defined]  # noqa: F821
