from datetime import date, datetime
from sqlalchemy import String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import BaseModel, utc_now


class EVCVisit(BaseModel):
    __tablename__ = "evc_visits"

    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="AWAITING_SCHEDULE", index=True)
    # Statuses: AWAITING_SCHEDULE, SCHEDULED, COMPLETED, REPORT_PENDING, REPORT_SUBMITTED, CANCELLED

    proposed_date: Mapped[date] = mapped_column(Date, nullable=True)
    confirmed_date: Mapped[date] = mapped_column(Date, nullable=True)
    completed_date: Mapped[date] = mapped_column(Date, nullable=True)
    report_submitted_date: Mapped[date] = mapped_column(Date, nullable=True)

    report_summary: Mapped[str] = mapped_column(Text, nullable=True)
    coordinator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    delay_reason: Mapped[str] = mapped_column(Text, nullable=True)
    report_file_ref: Mapped[str] = mapped_column(String(255), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    application = relationship("Application", back_populates="evc_visits")
    coordinator = relationship("User")
    experts = relationship("EVCExpert", back_populates="visit")


class EVCExpert(BaseModel):
    __tablename__ = "evc_experts"

    visit_id: Mapped[str] = mapped_column(String(36), ForeignKey("evc_visits.id"), nullable=False)
    expert_name: Mapped[str] = mapped_column(String(100), nullable=False)
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    organization: Mapped[str] = mapped_column(String(150), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ASSIGNED")

    visit = relationship("EVCVisit", back_populates="experts")
