from datetime import date, datetime
from sqlalchemy import String, Text, Date, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import BaseModel, utc_now


class ComplianceObligation(BaseModel):
    __tablename__ = "compliance_obligations"

    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=True)
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    condition_source: Mapped[str] = mapped_column(String(150), default="APH Condition Precedent")
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(50), default="UPCOMING", index=True)
    # Statuses: UPCOMING, DUE_SOON, SUBMITTED, UNDER_VERIFICATION, VERIFIED, DEFICIENT, OVERDUE, CLOSED, SUPERSEDED

    responsible_person: Mapped[str] = mapped_column(String(100), nullable=True)
    reviewer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    review_comments: Mapped[str] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    application = relationship("Application", back_populates="compliance_obligations")
    institution = relationship("Institution", back_populates="compliance_obligations")
    reviewer = relationship("User")
    evidences = relationship("ComplianceEvidence", back_populates="obligation", order_by="ComplianceEvidence.created_at.desc()")


class ComplianceEvidence(BaseModel):
    __tablename__ = "compliance_evidences"

    obligation_id: Mapped[str] = mapped_column(String(36), ForeignKey("compliance_obligations.id"), nullable=False)
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    submitted_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    submission_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Invariant: Uploading evidence enters SUBMITTED, NEVER automatically VERIFIED
    verification_status: Mapped[str] = mapped_column(String(50), default="SUBMITTED")
    # SUBMITTED, UNDER_VERIFICATION, VERIFIED, DEFICIENT
    verified_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)

    obligation = relationship("ComplianceObligation", back_populates="evidences")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])

