from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import BaseModel


class Institution(BaseModel):
    __tablename__ = "institutions"

    aicte_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    region_id: Mapped[str] = mapped_column(String(36), ForeignKey("regions.id"), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    district: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(30), nullable=True)

    region = relationship("Region", back_populates="institutions")
    users = relationship("User", back_populates="institution")
    applications = relationship("Application", back_populates="institution")
    compliance_obligations = relationship("ComplianceObligation", back_populates="institution")
    documents = relationship("DocumentRegistry", back_populates="institution")

