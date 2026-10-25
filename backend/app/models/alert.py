from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import BaseModel


class Alert(BaseModel):
    __tablename__ = "alerts"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # APPLICATION, EVC, COMPLIANCE, DOCUMENT
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), nullable=True)
    region_id: Mapped[str] = mapped_column(String(36), ForeignKey("regions.id"), nullable=True)

    alert_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(30), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Idempotency constraint prevents duplicate alerts on repeated evaluation runs
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)

    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0)

    institution = relationship("Institution")
    region = relationship("Region")
    acknowledged_by = relationship("User")
    notifications = relationship("NotificationOutbox", back_populates="alert")
