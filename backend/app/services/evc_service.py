from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.models.application import Application
from backend.app.models.user import User
from backend.app.core.storage import storage_service
from backend.app.services.audit_service import audit_service


class EVCService:
    @staticmethod
    def get_scoped_visits(
        db: Session,
        user: User,
        status: Optional[str] = None,
        region_id: Optional[str] = None
    ) -> List[EVCVisit]:
        query = db.query(EVCVisit).join(Application)

        # Server-enforced scope boundaries
        if user.role == "INST_ADMIN":
            if not user.institution_id:
                return []
            query = query.filter(Application.institution_id == user.institution_id)
        elif user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            if not user.region_id:
                return []
            query = query.filter(Application.region_id == user.region_id)
        elif user.role in ["COMMITTEE_MBR", "COMM_MEMBER"]:
            query = query.join(EVCExpert).filter(EVCExpert.contact_email == user.email)

        # Cross-regional users may optionally filter by region
        if region_id and user.role not in ["INST_ADMIN", "RO_OFFICER", "REGIONAL_DIR", "EVC_COORD", "COMMITTEE_MBR", "COMM_MEMBER"]:
            query = query.filter(Application.region_id == region_id)

        if status:
            query = query.filter(EVCVisit.status == status.upper())

        return query.order_by(desc(EVCVisit.created_at)).all()

    @staticmethod
    def schedule_visit(
        db: Session,
        application_id: str,
        proposed_date: date,
        coordinator_id: Optional[str],
        user: User
    ) -> EVCVisit:
        # Check permissions
        if user.role not in ["EVC_COORD", "RO_OFFICER", "BUREAU_OFFICER", "REGIONAL_DIR", "COMP_AUTH", "SYS_ADMIN"]:
            raise PermissionError("Access denied: You do not have permission to schedule EVC inspections")

        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError("Application not found")

        # Region scope check
        if user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            if not user.region_id or app.region_id != user.region_id:
                raise PermissionError("Security violation: Cannot schedule EVC for application outside your assigned region")

        visit = db.query(EVCVisit).filter(EVCVisit.application_id == application_id).first()
        if not visit:
            visit = EVCVisit(
                application_id=application_id,
                proposed_date=proposed_date,
                confirmed_date=proposed_date,
                coordinator_id=coordinator_id or user.id,
                status="SCHEDULED"
            )
            db.add(visit)
        else:
            visit.proposed_date = proposed_date
            visit.confirmed_date = proposed_date
            if coordinator_id:
                visit.coordinator_id = coordinator_id
            visit.status = "SCHEDULED"

        db.flush()

        audit_service.record_event(
            db=db,
            actor_role=user.role,
            actor_id=user.id,
            action="EVC_VISIT_SCHEDULED",
            entity_type="EVC_VISIT",
            entity_id=visit.id,
            new_state="SCHEDULED",
            details={
                "application_id": app.id,
                "application_no": app.application_no,
                "confirmed_date": proposed_date.isoformat(),
                "coordinator_id": visit.coordinator_id
            }
        )

        db.commit()
        db.refresh(visit)
        return visit

    @staticmethod
    def reschedule_visit(
        db: Session,
        visit_id: str,
        new_date: date,
        delay_reason: str,
        user: User
    ) -> EVCVisit:
        if not delay_reason or not delay_reason.strip():
            raise ValueError("Reschedule rejected: Mandatory justification reason is required for any EVC date change")

        visit = db.query(EVCVisit).filter(EVCVisit.id == visit_id).first()
        if not visit:
            raise ValueError("EVC Visit not found")

        # Scope check
        app = visit.application
        if user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            if not user.region_id or app.region_id != user.region_id:
                raise PermissionError("Security violation: Cannot modify EVC outside assigned region")

        prev_date = visit.confirmed_date
        visit.confirmed_date = new_date
        visit.delay_reason = delay_reason.strip()
        visit.status = "SCHEDULED"

        audit_service.record_event(
            db=db,
            actor_role=user.role,
            actor_id=user.id,
            action="EVC_VISIT_RESCHEDULED",
            entity_type="EVC_VISIT",
            entity_id=visit.id,
            details={
                "previous_date": prev_date.isoformat() if prev_date else None,
                "new_date": new_date.isoformat(),
                "delay_reason": delay_reason
            }
        )

        db.commit()
        db.refresh(visit)
        return visit

    @staticmethod
    def assign_expert(
        db: Session,
        visit_id: str,
        expert_name: str,
        designation: str,
        organization: str,
        contact_email: str,
        user: User
    ) -> EVCExpert:
        visit = db.query(EVCVisit).filter(EVCVisit.id == visit_id).first()
        if not visit:
            raise ValueError("EVC Visit not found")

        app = visit.application
        if user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            if not user.region_id or app.region_id != user.region_id:
                raise PermissionError("Security violation: Cannot assign experts outside assigned region")

        expert = EVCExpert(
            visit_id=visit_id,
            expert_name=expert_name,
            designation=designation,
            organization=organization,
            contact_email=contact_email,
            status="ASSIGNED"
        )
        db.add(expert)
        db.flush()

        audit_service.record_event(
            db=db,
            actor_role=user.role,
            actor_id=user.id,
            action="EVC_EXPERT_ASSIGNED",
            entity_type="EVC_EXPERT",
            entity_id=expert.id,
            details={
                "visit_id": visit_id,
                "expert_name": expert_name,
                "organization": organization
            }
        )

        db.commit()
        db.refresh(expert)
        return expert

    @staticmethod
    def submit_report(
        db: Session,
        visit_id: str,
        report_summary: str,
        file_bytes: bytes,
        file_name: str,
        user: User
    ) -> EVCVisit:
        if not report_summary or not report_summary.strip():
            raise ValueError("Report submission requires inspection summary findings")

        visit = db.query(EVCVisit).filter(EVCVisit.id == visit_id).first()
        if not visit:
            raise ValueError("EVC Visit not found")

        app = visit.application
        if user.role in ["COMMITTEE_MBR", "COMM_MEMBER"]:
            is_expert = any(e.contact_email == user.email for e in visit.experts)
            if not is_expert:
                raise PermissionError("Security violation: Only assigned committee members can submit the inspection report")
        elif user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            if not user.region_id or app.region_id != user.region_id:
                raise PermissionError("Security violation: Cannot upload EVC report outside assigned region")

        # Save report file
        file_path, sha256_hash, file_size, content_type = storage_service.save_bytes(
            file_bytes=file_bytes,
            filename=file_name
        )

        visit.report_summary = report_summary.strip()
        visit.report_file_ref = file_path
        visit.report_submitted_date = date.today()
        visit.completed_date = date.today()
        visit.status = "REPORT_SUBMITTED"

        audit_service.record_event(
            db=db,
            actor_role=user.role,
            actor_id=user.id,
            action="EVC_REPORT_SUBMITTED",
            entity_type="EVC_VISIT",
            entity_id=visit.id,
            new_state="REPORT_SUBMITTED",
            details={
                "report_summary": report_summary[:200],
                "sha256_hash": sha256_hash,
                "file_size": file_size
            }
        )

        db.commit()
        db.refresh(visit)
        return visit
