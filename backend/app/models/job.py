from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import BaseModel, utc_now


class JobExecution(BaseModel):
    __tablename__ = "job_executions"

    job_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="RUNNING", index=True)  # RUNNING, SUCCESS, FAILED, MISSED
    items_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
