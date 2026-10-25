from datetime import date, datetime
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import BaseModel, utc_now


class DocumentRegistry(BaseModel):
    __tablename__ = "document_registry"

    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), nullable=False)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=True)

    document_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Categories: LEASE_DEED, LAND_TITLE, OCCUPANCY_CERT, FIRE_NOC, BUILDING_SAFETY, AICTE_AFFIDAVIT
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    current_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="VALID", index=True)
    # Statuses: VALID, EXPIRING_SOON, EXPIRED, SUPERSEDED, RENEWAL_SUBMITTED

    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    verified_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Version linkage for renewals
    previous_document_id: Mapped[str] = mapped_column(String(36), ForeignKey("document_registry.id"), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    institution = relationship("Institution", back_populates="documents")
    verified_by = relationship("User")
    previous_version = relationship("DocumentRegistry", remote_side="DocumentRegistry.id", backref="renewals")
