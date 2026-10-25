from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import BaseModel, utc_now


class AuditEvent(BaseModel):
    __tablename__ = "audit_events"

    sequence_no: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    actor_id: Mapped[str] = mapped_column(String(36), nullable=True)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    previous_state: Mapped[str] = mapped_column(String(100), nullable=True)
    new_state: Mapped[str] = mapped_column(String(100), nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")

    # Cryptographic hash chain for tamper evidence
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
