from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from backend.app.core.database import get_db
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User
from backend.app.models.alert import Alert
from backend.app.models.notification import NotificationOutbox
from backend.app.services.alert_service import AlertService


router = APIRouter(prefix="/api/alerts", tags=["Alerts & Deadlines"])


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    acknowledged_by_id: Optional[str] = None
    acknowledged_by_name: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    is_escalated: bool
    escalation_level: int
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    alert_id: str
    alert_title: Optional[str] = None
    recipient_user_id: Optional[str] = None
    recipient_email: str
    channel: str
    status: str
    retry_count: int
    last_error: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime


class EvaluationRequest(BaseModel):
    fail_notifications: bool = False
    simulated_date: Optional[str] = None  # ISO format string for testing downtime catch-up


@router.get("", response_model=List[AlertOut])
def list_alerts(
    is_acknowledged: Optional[bool] = None,
    severity: Optional[str] = None,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns alerts scoped to the authenticated user's institution or region.
    """
    alerts = AlertService.get_scoped_alerts(
        db=db,
        user=current_user,
        is_acknowledged=is_acknowledged,
        severity=severity,
        entity_type=entity_type
    )

    result = []
    for a in alerts:
        res = AlertOut(
            id=a.id,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            institution_id=a.institution_id,
            institution_name=a.institution.name if a.institution else None,
            region_id=a.region_id,
            region_name=a.region.name if a.region else None,
            alert_type=a.alert_type,
            severity=a.severity,
            title=a.title,
            message=a.message,
            idempotency_key=a.idempotency_key,
            is_acknowledged=a.is_acknowledged,
            acknowledged_by_id=a.acknowledged_by_id,
            acknowledged_by_name=a.acknowledged_by.full_name if a.acknowledged_by else None,
            acknowledged_at=a.acknowledged_at,
            is_escalated=a.is_escalated,
            escalation_level=a.escalation_level,
            created_at=a.created_at
        )
        result.append(res)
    return result


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Acknowledges an alert with scope validation.
    """
    try:
        alert = AlertService.acknowledge_alert(db=db, alert_id=alert_id, user=current_user)
        return AlertOut(
            id=alert.id,
            entity_type=alert.entity_type,
            entity_id=alert.entity_id,
            institution_id=alert.institution_id,
            institution_name=alert.institution.name if alert.institution else None,
            region_id=alert.region_id,
            region_name=alert.region.name if alert.region else None,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            idempotency_key=alert.idempotency_key,
            is_acknowledged=alert.is_acknowledged,
            acknowledged_by_id=alert.acknowledged_by_id,
            acknowledged_by_name=current_user.full_name,
            acknowledged_at=alert.acknowledged_at,
            is_escalated=alert.is_escalated,
            escalation_level=alert.escalation_level,
            created_at=alert.created_at
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/evaluate")
def trigger_deadline_evaluation(
    payload: Optional[EvaluationRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers an on-demand deadline and alert evaluation run across all entities.
    Idempotent: repeating this run does not create duplicate alerts.
    """
    # Any authenticated officer or admin can trigger evaluation
    simulated_dt = None
    fail_notif = False
    if payload:
        fail_notif = payload.fail_notifications
        if payload.simulated_date:
            try:
                simulated_dt = datetime.fromisoformat(payload.simulated_date)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid simulated_date ISO format")

    summary = AlertService.evaluate_and_generate_alerts(
        db=db,
        now=simulated_dt,
        fail_notifications=fail_notif
    )
    return summary


@router.get("/notifications", response_model=List[NotificationOut])
def list_notification_outbox(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns outbox notification delivery log.
    Institutions only see their own notifications; officers see regional/all.
    """
    query = db.query(NotificationOutbox).join(Alert)

    if current_user.role == "INST_ADMIN":
        query = query.filter(Alert.institution_id == current_user.institution_id)
    elif current_user.role in ["RO_OFFICER", "REGIONAL_DIR"]:
        query = query.filter(Alert.region_id == current_user.region_id)

    if status_filter:
        query = query.filter(NotificationOutbox.status == status_filter.upper())

    records = query.order_by(NotificationOutbox.created_at.desc()).limit(100).all()

    result = []
    for r in records:
        result.append(NotificationOut(
            id=r.id,
            alert_id=r.alert_id,
            alert_title=r.alert.title if r.alert else None,
            recipient_user_id=r.recipient_user_id,
            recipient_email=r.recipient_email,
            channel=r.channel,
            status=r.status,
            retry_count=r.retry_count,
            last_error=r.last_error,
            sent_at=r.sent_at,
            created_at=r.created_at
        ))
    return result


@router.post("/notifications/{notification_id}/retry", response_model=NotificationOut)
def retry_failed_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually retries a failed outbox notification.
    """
    try:
        record = AlertService.retry_notification(db=db, notification_id=notification_id, user=current_user)
        return NotificationOut(
            id=record.id,
            alert_id=record.alert_id,
            alert_title=record.alert.title if record.alert else None,
            recipient_user_id=record.recipient_user_id,
            recipient_email=record.recipient_email,
            channel=record.channel,
            status=record.status,
            retry_count=record.retry_count,
            last_error=record.last_error,
            sent_at=record.sent_at,
            created_at=record.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
