import uuid

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class AdminAudit(Base):
    __tablename__ = "admin_audit"
    __table_args__ = (
        Index("ix_admin_audit_actor", "actor_id"),
        Index("ix_admin_audit_entity", "entity", "entity_id"),
        Index("ix_admin_audit_payload_gin", "payload", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    actor: Mapped["User"] = relationship("User", back_populates="audit_entries")  # type: ignore[name-defined]  # noqa: F821
