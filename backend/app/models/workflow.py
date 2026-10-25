from sqlalchemy import String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import BaseModel


class WorkflowDefinition(BaseModel):
    __tablename__ = "workflow_definitions"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    aph_version: Mapped[str] = mapped_column(String(50), default="APH 2024-27")
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    stages = relationship("WorkflowStage", back_populates="workflow", order_by="WorkflowStage.sequence_order")


class WorkflowStage(BaseModel):
    __tablename__ = "workflow_stages"

    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_definitions.id"), nullable=False)
    stage_key: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, default=1)
    sla_days: Mapped[int] = mapped_column(Integer, default=7)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False)

    workflow = relationship("WorkflowDefinition", back_populates="stages")
