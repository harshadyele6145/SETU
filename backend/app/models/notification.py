from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import BaseModel


class NotificationOutbox(BaseModel):
    __tablename__ = "notifications"

    alert_id: Mapped[str] = mapped_column(String(36), ForeignKey("alerts.id"), nullable=False)
    recipient_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(120), nullable=False)
    channel: Mapped[str] = mapped_column(String(30), default="IN_APP")  # IN_APP, EMAIL_SIMULATED

    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    # PENDING, SENT, FAILED, RETRYING
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    alert = relationship("Alert", back_populates="notifications")
    recipient = relationship("User")
