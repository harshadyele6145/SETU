from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class AttentionFactor(BaseModel):
    factor_name: str
    weight: int
    points_awarded: int
    rationale: str


class AttentionQueueItem(BaseModel):
    application_id: str
    application_no: str
    institution_name: str
    region_name: str
    current_stage: str
    priority_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    composite_score: int
    days_in_stage: int
    days_to_deadline: int
    is_overdue: bool
    responsible_role: str
    assigned_officer: Optional[str] = None
    blocking_dependency: str
    recommended_action: str
    explanation: str
    factors: List[AttentionFactor]


class BottleneckItem(BaseModel):
    id: str
    case_type: str  # APPLICATION, EVC, COMPLIANCE
    reference_no: str
    institution_name: str
    region_name: str
    current_status: str
    holding_side: str  # "WAITING_ON_INSTITUTION" or "WAITING_ON_AICTE"
    responsible_party: str
    age_days: int
    deadline_days_remaining: int
    is_overdue: bool
    escalation_state: str
    blocker_reason: str
    next_permissible_action: str


class BottleneckSummary(BaseModel):
    total_exceptions: int
    waiting_on_institution: int
    waiting_on_aicte: int
    overdue_count: int
    critical_escalations: int
    items: List[BottleneckItem]
