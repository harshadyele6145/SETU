from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.alert import Alert
from backend.app.models.notification import NotificationOutbox
from backend.app.models.user import User
from backend.app.models.base import utc_now
from backend.app.services.deadline_service import DeadlineService
from backend.app.services.audit_service import AuditService


class AlertService:
    @staticmethod
    def evaluate_and_generate_alerts(
        db: Session, 
        now: Optional[datetime] = None,
        fail_notifications: bool = False
    ) -> Dict[str, Any]:
        """
        Runs comprehensive deadline evaluation across all domains, creates idempotent alerts,
        enqueues outbox notifications, and dispatches them.
        """
        if now is None:
            now = utc_now()

        app_candidates = DeadlineService.evaluate_application_deadlines(db, now)
        comp_candidates = DeadlineService.evaluate_compliance_deadlines(db, now)
        doc_candidates = DeadlineService.evaluate_document_deadlines(db, now)

        all_candidates = app_candidates + comp_candidates + doc_candidates

        new_alerts = 0
        skipped_duplicates = 0
        notifications_enqueued = 0

        for cand in all_candidates:
            key = cand["idempotency_key"]
            existing = db.query(Alert).filter(Alert.idempotency_key == key).first()
            if existing:
                skipped_duplicates += 1
                continue

            # Create new Alert
            alert = Alert(
                entity_type=cand["entity_type"],
                entity_id=cand["entity_id"],
                institution_id=cand.get("institution_id"),
                region_id=cand.get("region_id"),
                alert_type=cand["alert_type"],
                severity=cand.get("severity", "MEDIUM"),
                title=cand["title"],
                message=cand["message"],
                idempotency_key=key,
                is_escalated=cand.get("is_escalated", False),
                escalation_level=cand.get("escalation_level", 0)
            )
            db.add(alert)
            db.flush()
            new_alerts += 1

            # Determine recipients for notification outbox
            # 1. Institution Admin if institution is known
            if alert.institution_id:
                inst_admin = db.query(User).filter(
                    User.institution_id == alert.institution_id,
                    User.role == "INST_ADMIN"
                ).first()
                if inst_admin:
                    notif = NotificationOutbox(
                        alert_id=alert.id,
                        recipient_user_id=inst_admin.id,
                        recipient_email=inst_admin.email,
                        channel="EMAIL_SIMULATED",
                        status="PENDING"
                    )
                    db.add(notif)
                    notifications_enqueued += 1

            # 2. Regional Officer / Director if region is known and alert is severe/escalated
            if alert.region_id and (alert.severity in ["HIGH", "CRITICAL"] or alert.is_escalated):
                ro_officer = db.query(User).filter(
                    User.region_id == alert.region_id,
                    User.role.in_(["RO_OFFICER", "REGIONAL_DIR"])
                ).first()
                if ro_officer:
                    notif = NotificationOutbox(
                        alert_id=alert.id,
                        recipient_user_id=ro_officer.id,
                        recipient_email=ro_officer.email,
                        channel="EMAIL_SIMULATED",
                        status="PENDING"
                    )
                    db.add(notif)
                    notifications_enqueued += 1

        db.commit()

        # Dispatch pending notifications
        dispatch_res = AlertService.dispatch_notifications(
            db, 
            max_retries=3, 
            fail_simulation=fail_notifications
        )

        return {
            "scanned_application_candidates": len(app_candidates),
            "scanned_compliance_candidates": len(comp_candidates),
            "scanned_document_candidates": len(doc_candidates),
            "total_candidates_evaluated": len(all_candidates),
            "new_alerts_created": new_alerts,
            "duplicate_alerts_skipped": skipped_duplicates,
            "notifications_enqueued": notifications_enqueued,
            "dispatch_summary": dispatch_res
        }

    @staticmethod
    def dispatch_notifications(
        db: Session, 
        max_retries: int = 3, 
        fail_simulation: bool = False
    ) -> Dict[str, int]:
        """
        Processes pending and retrying messages in NotificationOutbox.
        Simulates email delivery or records simulated failure for testing outbox recovery.
        """
        pending = db.query(NotificationOutbox).filter(
            NotificationOutbox.status.in_(["PENDING", "RETRYING"])
        ).all()

        sent_count = 0
        failed_count = 0
        retrying_count = 0

        now = utc_now()

        for notif in pending:
            if fail_simulation:
                notif.retry_count += 1
                if notif.retry_count >= max_retries:
                    notif.status = "FAILED"
                    notif.last_error = f"Max delivery attempts ({max_retries}) exhausted: Simulated SMTP connection timeout."
                    failed_count += 1
                else:
                    notif.status = "RETRYING"
                    notif.last_error = f"Delivery attempt {notif.retry_count} failed: Simulated transient network drop."
                    retrying_count += 1
            else:
                notif.status = "SENT"
                notif.sent_at = now
                notif.last_error = None
                sent_count += 1

        db.commit()
        return {
            "processed": len(pending),
            "sent": sent_count,
            "failed": failed_count,
            "retrying": retrying_count
        }

    @staticmethod
    def get_scoped_alerts(
        db: Session,
        user: User,
        is_acknowledged: Optional[bool] = None,
        severity: Optional[str] = None,
        entity_type: Optional[str] = None
    ) -> List[Alert]:
        """
        Returns alerts filtered by the user's role and data scope.
        """
        query = db.query(Alert)

        # Scoping
        if user.role == "INST_ADMIN":
            if not user.institution_id:
                return []
            query = query.filter(Alert.institution_id == user.institution_id)
        elif user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            if not user.region_id:
                return []
            query = query.filter(Alert.region_id == user.region_id)
        elif user.role in ["COMMITTEE_MBR", "COMM_MEMBER"]:
            from backend.app.models.evc import EVCVisit, EVCExpert
            assigned_app_ids = [
                row[0] for row in db.query(EVCVisit.application_id)
                .join(EVCExpert)
                .filter(EVCExpert.contact_email == user.email)
                .all()
            ]
            if not assigned_app_ids:
                return []
            query = query.filter(Alert.entity_type == "APPLICATION", Alert.entity_id.in_(assigned_app_ids))
        # HQ roles, Auditors, Comp Auth see all alerts

        if is_acknowledged is not None:
            query = query.filter(Alert.is_acknowledged == is_acknowledged)

        if severity:
            query = query.filter(Alert.severity == severity.upper())

        if entity_type:
            query = query.filter(Alert.entity_type == entity_type.upper())

        return query.order_by(desc(Alert.created_at)).all()

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: str, user: User) -> Alert:
        """
        Marks an alert acknowledged with server-enforced role and scope validation.
        """
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise ValueError("Alert not found")

        # Verify scope
        if user.role == "INST_ADMIN" and alert.institution_id != user.institution_id:
            raise PermissionError("Access denied: You cannot acknowledge an alert for another institution")
        if user.role in ["RO_OFFICER", "REGIONAL_DIR"] and alert.region_id != user.region_id:
            raise PermissionError("Access denied: You cannot acknowledge an alert outside your assigned region")

        if alert.is_acknowledged:
            return alert

        alert.is_acknowledged = True
        alert.acknowledged_by_id = user.id
        alert.acknowledged_at = utc_now()

        # Record Audit event
        AuditService.record_event(
            db=db,
            actor_role=user.role,
            actor_id=user.id,
            action="ALERT_ACKNOWLEDGED",
            entity_type="ALERT",
            entity_id=alert.id,
            details={
                "alert_title": alert.title,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "idempotency_key": alert.idempotency_key
            }
        )

        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def retry_notification(db: Session, notification_id: str, user: User) -> NotificationOutbox:
        """
        Manually triggers a retry for a failed outbox message.
        """
        notif = db.query(NotificationOutbox).filter(NotificationOutbox.id == notification_id).first()
        if not notif:
            raise ValueError("Notification not found")

        notif.status = "PENDING"
        notif.retry_count = 0
        notif.last_error = None
        db.commit()

        # Dispatch
        AlertService.dispatch_notifications(db, max_retries=3, fail_simulation=False)
        db.refresh(notif)
        return notif
