from pydantic import BaseModel
from typing import List, Dict, Any


class DashboardSummary(BaseModel):
    total_applications: int
    active_in_pipeline: int
    pending_scrutiny: int
    evc_pending_scheduling: int
    evc_report_awaited: int
    decision_pending: int
    overdue_applications: int
    overdue_obligations: int
    documents_expiring_soon: int
    documents_expired: int
    unread_alerts_count: int

    stage_distribution: List[Dict[str, Any]]
    route_distribution: List[Dict[str, Any]]
    regional_workload: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]

