from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.models.application import Application
from backend.app.models.compliance import ComplianceObligation
from backend.app.models.document import DocumentRegistry
from backend.app.models.base import utc_now


# Gazetted Indian Public Holidays (Sample calendar for SLA business-day calculations)
INDIAN_PUBLIC_HOLIDAYS_2026 = {
    date(2026, 1, 26),  # Republic Day
    date(2026, 3, 25),  # Holi
    date(2026, 4, 14),  # Dr. Ambedkar Jayanti / Mahavir Jayanti
    date(2026, 8, 15),  # Independence Day
    date(2026, 10, 2),  # Mahatma Gandhi Jayanti
    date(2026, 10, 20), # Dussehra
    date(2026, 11, 8),  # Diwali
    date(2026, 12, 25), # Christmas
}


def is_business_day(d: date, holidays: Optional[set] = None) -> bool:
    """Returns True if the date is a weekday (Monday-Friday) and not a public holiday."""
    if holidays is None:
        holidays = INDIAN_PUBLIC_HOLIDAYS_2026
    # Monday is 0 and Sunday is 6
    if d.weekday() >= 5:
        return False
    return d not in holidays


def add_business_days(start_date: datetime, business_days: int) -> datetime:
    """Adds a given number of working business days to a timestamp."""
    current = start_date
    added = 0
    while added < business_days:
        current += timedelta(days=1)
        if is_business_day(current.date()):
            added += 1
    return current


def calculate_days_difference(target_dt: datetime | date, reference_dt: Optional[datetime] = None) -> int:
    """Calculates remaining days until target_dt. Negative if past/overdue."""
    if reference_dt is None:
        reference_dt = utc_now()
    
    if isinstance(target_dt, datetime):
        # Ensure UTC timezone awareness
        if target_dt.tzinfo is None:
            target_dt = target_dt.replace(tzinfo=timezone.utc)
        if reference_dt.tzinfo is None:
            reference_dt = reference_dt.replace(tzinfo=timezone.utc)
        diff = target_dt - reference_dt
        return int(diff.total_seconds() // 86400)
    else:
        # Date object
        ref_date = reference_dt.date() if isinstance(reference_dt, datetime) else reference_dt
        return (target_dt - ref_date).days


class DeadlineService:
    @staticmethod
    def evaluate_application_deadlines(db: Session, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Scans all active applications and returns candidates for alert creation.
        Does not create alerts directly; delegates to AlertService for idempotent persistence.
        """
        if now is None:
            now = utc_now()

        active_apps = db.query(Application).filter(
            Application.status.notin_(["APPROVED", "REJECTED"]),
            Application.is_paused.is_(False)
        ).all()

        candidates = []

        for app in active_apps:
            # If current_sla_deadline is not set, calculate from current_stage
            if not app.current_sla_deadline:
                sla_days = app.current_stage.sla_days if app.current_stage else 15
                stage_entered = app.stage_entered_at or app.submitted_at or now
                app.current_sla_deadline = add_business_days(stage_entered, sla_days)
                db.flush()

            deadline = app.current_sla_deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)

            days_remaining = calculate_days_difference(deadline, now)

            # Determine alert window triggers
            if days_remaining < 0:
                days_overdue = abs(days_remaining)
                escalation = 3 if days_overdue >= 7 else (2 if days_overdue >= 3 else 1)
                severity = "CRITICAL" if days_overdue >= 3 else "HIGH"
                candidates.append({
                    "entity_type": "APPLICATION",
                    "entity_id": app.id,
                    "institution_id": app.institution_id,
                    "region_id": app.region_id,
                    "alert_type": "SLA_BREACH",
                    "window": "overdue",
                    "severity": severity,
                    "title": f"SLA Breached: Application {app.application_no} overdue by {days_overdue} days",
                    "message": f"Stage '{app.current_stage.name if app.current_stage else 'Processing'}' exceeded SLA deadline on {deadline.strftime('%Y-%m-%d')}. Escalation Level: {escalation}.",
                    "idempotency_key": f"APPLICATION:{app.id}:SLA_BREACH:overdue",
                    "is_escalated": True,
                    "escalation_level": escalation,
                    "days_remaining": days_remaining
                })
            elif days_remaining <= 1:
                candidates.append({
                    "entity_type": "APPLICATION",
                    "entity_id": app.id,
                    "institution_id": app.institution_id,
                    "region_id": app.region_id,
                    "alert_type": "SLA_WINDOW",
                    "window": "1d",
                    "severity": "HIGH",
                    "title": f"Urgent SLA Warning: Application {app.application_no} due in 24 hours",
                    "message": f"Target deadline for stage '{app.current_stage.name if app.current_stage else 'Processing'}' is {deadline.strftime('%Y-%m-%d')}.",
                    "idempotency_key": f"APPLICATION:{app.id}:SLA_WINDOW:1d",
                    "is_escalated": False,
                    "escalation_level": 0,
                    "days_remaining": days_remaining
                })
            elif days_remaining <= 7:
                candidates.append({
                    "entity_type": "APPLICATION",
                    "entity_id": app.id,
                    "institution_id": app.institution_id,
                    "region_id": app.region_id,
                    "alert_type": "SLA_WINDOW",
                    "window": "7d",
                    "severity": "MEDIUM",
                    "title": f"SLA Notice: Application {app.application_no} due in {days_remaining} days",
                    "message": f"Stage deadline approaching on {deadline.strftime('%Y-%m-%d')}.",
                    "idempotency_key": f"APPLICATION:{app.id}:SLA_WINDOW:7d",
                    "is_escalated": False,
                    "escalation_level": 0,
                    "days_remaining": days_remaining
                })
            elif days_remaining <= 15:
                candidates.append({
                    "entity_type": "APPLICATION",
                    "entity_id": app.id,
                    "institution_id": app.institution_id,
                    "region_id": app.region_id,
                    "alert_type": "SLA_WINDOW",
                    "window": "15d",
                    "severity": "LOW",
                    "title": f"SLA Advisory: Application {app.application_no} due in {days_remaining} days",
                    "message": f"Planned scrutiny milestone date is {deadline.strftime('%Y-%m-%d')}.",
                    "idempotency_key": f"APPLICATION:{app.id}:SLA_WINDOW:15d",
                    "is_escalated": False,
                    "escalation_level": 0,
                    "days_remaining": days_remaining
                })

        return candidates

    @staticmethod
    def evaluate_compliance_deadlines(db: Session, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Scans all pending and active compliance obligations and updates status and alert windows.
        """
        if now is None:
            now = utc_now()
        today = now.date()

        obligations = db.query(ComplianceObligation).filter(
            ComplianceObligation.status.notin_(["VERIFIED", "CLOSED"])
        ).all()

        candidates = []

        for ob in obligations:
            days_remaining = calculate_days_difference(ob.due_date, now)
            reg_id = ob.institution.region_id if ob.institution else None

            if days_remaining < 0:
                if ob.status != "SUBMITTED":
                    ob.status = "OVERDUE"
                days_overdue = abs(days_remaining)
                severity = "CRITICAL" if days_overdue >= 7 else "HIGH"
                candidates.append({
                    "entity_type": "COMPLIANCE",
                    "entity_id": ob.id,
                    "institution_id": ob.institution_id,
                    "region_id": reg_id,
                    "alert_type": "COMPLIANCE_BREACH",
                    "window": "overdue",
                    "severity": severity,
                    "title": f"Compliance Overdue: {ob.title} ({days_overdue} days past due)",
                    "message": f"Mandatory undertaking '{ob.title}' for category {ob.category} was due on {ob.due_date}. Failure to comply may affect approval status.",
                    "idempotency_key": f"COMPLIANCE:{ob.id}:DUE_BREACH:overdue",
                    "is_escalated": True,
                    "escalation_level": 2 if days_overdue >= 7 else 1,
                    "days_remaining": days_remaining
                })
            elif days_remaining <= 1:
                candidates.append({
                    "entity_type": "COMPLIANCE",
                    "entity_id": ob.id,
                    "institution_id": ob.institution_id,
                    "region_id": reg_id,
                    "alert_type": "COMPLIANCE_WINDOW",
                    "window": "1d",
                    "severity": "HIGH",
                    "title": f"Compliance Due Tomorrow: {ob.title}",
                    "message": f"Condition precedent due on {ob.due_date}. Please upload proof of compliance.",
                    "idempotency_key": f"COMPLIANCE:{ob.id}:DUE_WINDOW:1d",
                    "is_escalated": False,
                    "escalation_level": 0,
                    "days_remaining": days_remaining
                })
            elif days_remaining <= 7:
                if ob.status == "UPCOMING":
                    ob.status = "DUE_SOON"
                candidates.append({
                    "entity_type": "COMPLIANCE",
                    "entity_id": ob.id,
                    "institution_id": ob.institution_id,
                    "region_id": reg_id,
                    "alert_type": "COMPLIANCE_WINDOW",
                    "window": "7d",
                    "severity": "MEDIUM",
                    "title": f"Compliance Notice: {ob.title} due in {days_remaining} days",
                    "message": f"Due date is {ob.due_date}. Proof of undertaking required.",
                    "idempotency_key": f"COMPLIANCE:{ob.id}:DUE_WINDOW:7d",
                    "is_escalated": False,
                    "escalation_level": 0,
                    "days_remaining": days_remaining
                })
            elif days_remaining <= 30:
                candidates.append({
                    "entity_type": "COMPLIANCE",
                    "entity_id": ob.id,
                    "institution_id": ob.institution_id,
                    "region_id": reg_id,
                    "alert_type": "COMPLIANCE_WINDOW",
                    "window": "30d",
                    "severity": "LOW",
                    "title": f"Upcoming Compliance Milestone: {ob.title} due in {days_remaining} days",
                    "message": f"Due date: {ob.due_date}.",
                    "idempotency_key": f"COMPLIANCE:{ob.id}:DUE_WINDOW:30d",
                    "is_escalated": False,
                    "escalation_level": 0,
                    "days_remaining": days_remaining
                })

        db.flush()
        return candidates

    @staticmethod
    def evaluate_document_deadlines(db: Session, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Scans all registered certificates/deeds and identifies documents approaching expiry or expired.
        """
        if now is None:
            now = utc_now()
        today = now.date()

        docs = db.query(DocumentRegistry).filter(
            DocumentRegistry.status.notin_(["SUPERSEDED"])
        ).all()

        candidates = []

        for doc in docs:
            days_remaining = calculate_days_difference(doc.expiry_date, now)
            reg_id = doc.institution.region_id if doc.institution else None

            if days_remaining < 0:
                if doc.status not in ["RENEWAL_SUBMITTED", "SUPERSEDED"]:
                    doc.status = "EXPIRED"
                days_expired = abs(days_remaining)
                candidates.append({
                    "entity_type": "DOCUMENT",
                    "entity_id": doc.id,
                    "institution_id": doc.institution_id,
                    "region_id": reg_id,
                    "alert_type": "DOCUMENT_EXPIRED",
                    "window": "expired",
                    "severity": "CRITICAL",
                    "title": f"Document Expired: {doc.title} ({days_expired} days ago)",
                    "message": f"Mandatory document '{doc.title}' expired on {doc.expiry_date}. Immediate replacement or renewal deed upload required.",
                    "idempotency_key": f"DOCUMENT:{doc.id}:EXPIRY_BREACH:expired",
                    "is_escalated": True,
                    "escalation_level": 2 if days_expired >= 30 else 1,
                    "days_remaining": days_remaining
                })
            elif days_remaining <= 30:
                if doc.status == "VALID":
                    doc.status = "EXPIRING_SOON"
                candidates.append({
                    "entity_type": "DOCUMENT",
                    "entity_id": doc.id,
                    "institution_id": doc.institution_id,
                    "region_id": reg_id,
                    "alert_type": "DOCUMENT_EXPIRING",
                    "window": "30d",
                    "severity": "HIGH",
                    "title": f"Document Expiring Soon: {doc.title} in {days_remaining} days",
                    "message": f"Validity terminates on {doc.expiry_date}. Renewal deed must be initiated.",
                    "idempotency_key": f"DOCUMENT:{doc.id}:EXPIRY_WINDOW:30d",
                    "is_escalated": False,
                    "escalation_level": 0,
                    "days_remaining": days_remaining
                })
            elif days_remaining <= 90:
                candidates.append({
                    "entity_type": "DOCUMENT",
                    "entity_id": doc.id,
                    "institution_id": doc.institution_id,
                    "region_id": reg_id,
                    "alert_type": "DOCUMENT_EXPIRING",
                    "window": "90d",
                    "severity": "MEDIUM",
                    "title": f"Document Expiry Warning: {doc.title} in {days_remaining} days",
                    "message": f"Expiry date {doc.expiry_date}. Prepare renewal documentation.",
                    "idempotency_key": f"DOCUMENT:{doc.id}:EXPIRY_WINDOW:90d",
                    "is_escalated": False,
                    "escalation_level": 0,
                    "days_remaining": days_remaining
                })

        db.flush()
        return candidates
