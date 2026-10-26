import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DataProvenanceMixin:
    """
    Data Provenance & Trust Classification Mixin (SIH26262 Reliability Architecture)
    Classifies datasets into:
    - Category A: Synthetic Seed (source_system="SYNTHETIC_SEED", is_synthetic=True)
    - Category B: Public Reference (source_system="AICTE_ONOD_PUBLIC", is_synthetic=False)
    - Category C: Real Operational (source_system="SETU_OPERATIONAL", is_synthetic=False)
    """
    source_system: Mapped[str] = mapped_column(String(50), default="SETU_OPERATIONAL", nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    source_record_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    sync_status: Mapped[str] = mapped_column(String(50), default="SYNCED", nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


