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
