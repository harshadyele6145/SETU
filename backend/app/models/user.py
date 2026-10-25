from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Scoping keys
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), nullable=True)
    region_id: Mapped[str] = mapped_column(String(36), ForeignKey("regions.id"), nullable=True)

    institution = relationship("Institution", back_populates="users")
    region = relationship("Region", back_populates="users")
    assigned_applications = relationship("Application", back_populates="assigned_officer", foreign_keys="Application.assigned_officer_id")

