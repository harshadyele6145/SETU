from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import BaseModel, utc_now


class Application(BaseModel):
    __tablename__ = "applications"

    application_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), nullable=False)
    region_id: Mapped[str] = mapped_column(String(36), ForeignKey("regions.id"), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), default="2026-2027")
    application_type: Mapped[str] = mapped_column(String(100), default="Extension of Approval (EoA)")
    route: Mapped[str] = mapped_column(String(50), default="ROUTE_A")  # ROUTE_A, ROUTE_B, ROUTE_C, ROUTE_D

    current_stage_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_stages.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", index=True)
    assigned_officer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    stage_entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    current_sla_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    return_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    institution = relationship("Institution", back_populates="applications")
    region = relationship("Region", back_populates="applications")
    current_stage = relationship("WorkflowStage")
    assigned_officer = relationship("User", back_populates="assigned_applications", foreign_keys=[assigned_officer_id])
    history = relationship("ApplicationHistory", back_populates="application", order_by="ApplicationHistory.created_at.desc()")
    evc_visits = relationship("EVCVisit", back_populates="application")
    compliance_obligations = relationship("ComplianceObligation", back_populates="application")


class ApplicationHistory(BaseModel):
    __tablename__ = "application_history"

    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=False)
    from_stage_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_stages.id"), nullable=True)
    to_stage_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_stages.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    comments: Mapped[str] = mapped_column(Text, nullable=True)

    application = relationship("Application", back_populates="history")
    actor = relationship("User")
    from_stage = relationship("WorkflowStage", foreign_keys=[from_stage_id])
    to_stage = relationship("WorkflowStage", foreign_keys=[to_stage_id])

