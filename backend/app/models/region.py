from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import BaseModel


class Region(BaseModel):
    __tablename__ = "regions"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    states_covered: Mapped[str] = mapped_column(String(255), nullable=False)

    institutions = relationship("Institution", back_populates="region")
    users = relationship("User", back_populates="region")
    applications = relationship("Application", back_populates="region")
