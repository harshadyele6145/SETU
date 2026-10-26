from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ApplicationCreate(BaseModel):
    academic_year: str = "2026-2027"
    application_type: str = "Extension of Approval (EoA)"
    route: str = "ROUTE_A"  # ROUTE_A, ROUTE_B, ROUTE_C, ROUTE_D


class ApplicationTransitionRequest(BaseModel):
    action: str
    target_stage_key: Optional[str] = None
    comments: Optional[str] = None


class ApplicationReturnRequest(BaseModel):
    comments: str  # Mandatory deficiency reason!


class ApplicationReassignRequest(BaseModel):
    officer_id: str
    comments: Optional[str] = None


class ApplicationHistoryItem(BaseModel):
    id: str
    action: str
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    from_stage: Optional[str] = None
    to_stage: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationResponse(BaseModel):
    id: str
    application_no: str
    institution_id: str
    institution_name: Optional[str] = None
    institution_aicte_id: Optional[str] = None
    region_id: str
    region_name: Optional[str] = None
    academic_year: str
    application_type: str
    route: str
    status: str
    current_stage_key: Optional[str] = None
    current_stage_name: Optional[str] = None
    assigned_officer_id: Optional[str] = None
    assigned_officer_name: Optional[str] = None
    submitted_at: datetime
    stage_entered_at: datetime
    current_sla_deadline: Optional[datetime] = None
    is_paused: bool = False
    return_count: int = 0
    days_in_stage: int = 0
    total_days: int = 0

    model_config = ConfigDict(from_attributes=True)


class ApplicationDetailResponse(ApplicationResponse):
    history: List[ApplicationHistoryItem] = []


class PermittedAction(BaseModel):
    action_key: str
    action_label: str
    target_stage_key: Optional[str] = None
    endpoint: str
    http_method: str = "POST"
    allowed_roles: List[str]
    is_permitted_for_user: bool
    description: str


class AccountabilityBlocker(BaseModel):
    type: str  # COMPLIANCE or DOCUMENT
    title: str
    status: str
    detail: str
    severity: str  # CRITICAL, HIGH, MEDIUM


class ApplicationAccountabilityResponse(BaseModel):
    application_id: str
    application_no: str
    institution_name: str
    institution_aicte_id: Optional[str] = None
    region_name: str
    route: str
    status: str
    current_stage_name: str
    stage_entered_at: datetime
    days_in_stage: int
    sla_limit_days: int
    deadline: Optional[datetime] = None
    days_remaining: int
    is_overdue: bool
    holding_party: str  # WAITING_ON_INSTITUTION vs WAITING_ON_AICTE
    holding_party_label: str
    holding_responsible_role: str
    assigned_officer_name: Optional[str] = None
    return_count: int = 0
    current_user_role: str
    current_user_can_act: bool
    permitted_next_actions: List[PermittedAction] = []
    attention_score: int
    attention_tier: str
    attention_factors: List[str] = []
    blockers: List[AccountabilityBlocker] = []
    audit_event_count: int = 0
    latest_audit_hash: Optional[str] = None
