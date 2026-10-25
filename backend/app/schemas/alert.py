from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class AlertResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    region_id: Optional[str] = None
    region_name: Optional[str] = None
    alert_type: str
    severity: str
    title: str
    message: str
    idempotency_key: str
    is_acknowledged: bool
    acknowledged_by_name: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    is_escalated: bool
    escalation_level: int
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationItemResponse(BaseModel):
    id: str
    alert_id: str
    recipient_email: str
    channel: str
    status: str
    retry_count: int
    last_error: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertEvaluateResult(BaseModel):
    evaluated_at: datetime
    applications_evaluated: int
    evc_evaluated: int
    compliance_evaluated: int
    documents_evaluated: int
    new_alerts_created: int
    notifications_dispatched: int
