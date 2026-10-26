import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.models.application import Application, ApplicationHistory
from backend.app.models.workflow import WorkflowDefinition, WorkflowStage
from backend.app.models.institution import Institution
from backend.app.models.user import User
from backend.app.core.security import UserRole
from backend.app.services.auth_service import (
    enforce_institution_scope,
    enforce_region_scope,
    require_statutory_authority
)
from backend.app.services.audit_service import audit_service


# Route state transition graph definitions
ROUTE_TRANSITIONS: Dict[str, Dict[str, List[str]]] = {
    "ROUTE_A": {
        "DRAFT": ["SUBMITTED"],
        "SUBMITTED": ["UNDER_SCRUTINY", "SCRUTINY_QUEUE"],
        "SCRUTINY_QUEUE": ["UNDER_SCRUTINY"],
        "UNDER_SCRUTINY": ["SCRUTINY_DEFICIENT", "SCRUTINY_RECOMMENDED"],
        "SCRUTINY_DEFICIENT": ["UNDER_SCRUTINY"],
        "SCRUTINY_RECOMMENDED": ["DECISION_PENDING"],
        "DECISION_PENDING": ["APPROVED", "REJECTED"],
    },
    "ROUTE_B": {
        "DRAFT": ["SUBMITTED"],
        "SUBMITTED": ["UNDER_SCRUTINY", "SCRUTINY_QUEUE"],
        "SCRUTINY_QUEUE": ["UNDER_SCRUTINY"],
        "UNDER_SCRUTINY": ["SCRUTINY_DEFICIENT", "EVC_QUEUE"],
        "SCRUTINY_DEFICIENT": ["UNDER_SCRUTINY"],
        "EVC_QUEUE": ["EVC_SCHEDULED"],
        "EVC_SCHEDULED": ["EVC_COMPLETED"],
        "EVC_COMPLETED": ["EVC_REPORT_SUBMITTED"],
        "EVC_REPORT_SUBMITTED": ["DECISION_PENDING", "SHC_QUEUE"],
        "DECISION_PENDING": ["APPROVED", "REJECTED"],
    },
    "ROUTE_C": {
        "DRAFT": ["SUBMITTED"],
        "SUBMITTED": ["EVC_QUEUE"],
        "EVC_QUEUE": ["EVC_SCHEDULED"],
        "EVC_SCHEDULED": ["EVC_COMPLETED"],
        "EVC_COMPLETED": ["SHC_QUEUE"],
        "SHC_QUEUE": ["SAC_APPEAL", "DECISION_PENDING"],
        "SAC_APPEAL": ["DECISION_PENDING"],
        "DECISION_PENDING": ["APPROVED", "REJECTED"],
    },
    "ROUTE_D": {
        "DRAFT": ["SUBMITTED"],
        "SUBMITTED": ["EVC_QUEUE"],
        "EVC_QUEUE": ["EVC_SCHEDULED"],
        "EVC_SCHEDULED": ["EVC_COMPLETED"],
        "EVC_COMPLETED": ["DECISION_PENDING"],
        "DECISION_PENDING": ["APPROVED", "REJECTED"],
    }
}

# Role permissions required to transition into/out of specific stages
STAGE_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "SUBMITTED": [UserRole.INST_ADMIN.value],
    "UNDER_SCRUTINY": [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.BO_OFFICER.value, UserRole.BUREAU_OFFICER.value, UserRole.COMM_MEMBER.value, UserRole.COMMITTEE_MBR.value, UserRole.INST_ADMIN.value],
    "SCRUTINY_DEFICIENT": [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.BO_OFFICER.value, UserRole.BUREAU_OFFICER.value, UserRole.COMM_MEMBER.value, UserRole.COMMITTEE_MBR.value],
    "SCRUTINY_RECOMMENDED": [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.BO_OFFICER.value, UserRole.BUREAU_OFFICER.value],
    "EVC_QUEUE": [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.BO_OFFICER.value, UserRole.BUREAU_OFFICER.value],
    "EVC_SCHEDULED": [UserRole.EVC_COORD.value, UserRole.BO_OFFICER.value, UserRole.BUREAU_OFFICER.value],
    "EVC_COMPLETED": [UserRole.EVC_COORD.value, UserRole.COMM_MEMBER.value, UserRole.COMMITTEE_MBR.value],
    "EVC_REPORT_SUBMITTED": [UserRole.EVC_COORD.value, UserRole.COMM_MEMBER.value, UserRole.COMMITTEE_MBR.value],
    "SHC_QUEUE": [UserRole.BO_OFFICER.value, UserRole.BUREAU_OFFICER.value, UserRole.COMM_MEMBER.value, UserRole.COMMITTEE_MBR.value],
    "SAC_APPEAL": [UserRole.BO_OFFICER.value, UserRole.BUREAU_OFFICER.value, UserRole.COMM_MEMBER.value, UserRole.COMMITTEE_MBR.value, UserRole.INST_ADMIN.value],
    "DECISION_PENDING": [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.BO_OFFICER.value, UserRole.BUREAU_OFFICER.value, UserRole.COMM_MEMBER.value, UserRole.COMMITTEE_MBR.value],
    "APPROVED": [UserRole.COMP_AUTH.value],  # Invariant: ONLY Competent Authority
    "REJECTED": [UserRole.COMP_AUTH.value],  # Invariant: ONLY Competent Authority
}


class WorkflowEngine:
    @staticmethod
    def get_stage_by_key(db: Session, workflow_code: str, stage_key: str) -> Optional[WorkflowStage]:
        stmt = (
            select(WorkflowStage)
            .join(WorkflowDefinition, WorkflowStage.workflow_id == WorkflowDefinition.id)
            .where(WorkflowDefinition.code == workflow_code, WorkflowStage.stage_key == stage_key)
        )
        return db.execute(stmt).scalar_one_or_none()

    @classmethod
    def create_application(
        cls,
        db: Session,
        institution_id: str,
        academic_year: str,
        application_type: str,
        route: str,
        actor: User
    ) -> Application:
        enforce_institution_scope(actor, institution_id)

        inst = db.get(Institution, institution_id)
        if not inst:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

        # Generate unique application number
        app_no = f"AICTE-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
        initial_stage = cls.get_stage_by_key(db, route, "DRAFT")

        now = datetime.now(timezone.utc)
        application = Application(
            application_no=app_no,
            institution_id=institution_id,
            region_id=inst.region_id,
            academic_year=academic_year,
            application_type=application_type,
            route=route,
            current_stage_id=initial_stage.id if initial_stage else None,
            status="DRAFT",
            submitted_at=now,
            stage_entered_at=now,
            current_sla_deadline=None
        )
        db.add(application)
        db.flush()

        # Audit
        audit_service.record_event(
            db=db,
            actor_role=actor.role,
            action="APPLICATION_CREATED",
            entity_type="APPLICATION",
            entity_id=application.id,
            actor_id=actor.id,
            new_state="DRAFT",
            details={"application_no": app_no, "route": route}
        )

        return application

    @classmethod
    def submit_application(cls, db: Session, application_id: str, actor: User) -> Application:
        app = db.get(Application, application_id)
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        if actor.role != UserRole.INST_ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: Only an authorized Institution Administrator can submit an application."
            )
        enforce_institution_scope(actor, app.institution_id)

        if app.status != "DRAFT":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot submit application in status: {app.status}")

        next_stage_key = "SUBMITTED"
        next_stage = cls.get_stage_by_key(db, app.route, next_stage_key)
        if not next_stage:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stage {next_stage_key} not configured for route {app.route}")

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=next_stage.sla_days)

        history = ApplicationHistory(
            application_id=app.id,
            from_stage_id=app.current_stage_id,
            to_stage_id=next_stage.id,
            action="SUBMIT_APPLICATION",
            actor_id=actor.id,
            comments="Application formally submitted by institution."
        )
        db.add(history)

        prev_status = app.status
        app.current_stage_id = next_stage.id
        app.status = next_stage_key
        app.submitted_at = now
        app.stage_entered_at = now
        app.current_sla_deadline = deadline

        audit_service.record_event(
            db=db,
            actor_role=actor.role,
            action="APPLICATION_SUBMITTED",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=actor.id,
            previous_state=prev_status,
            new_state=next_stage_key,
            details={"application_no": app.application_no, "deadline": deadline.isoformat()}
        )

        db.commit()
        db.refresh(app)
        return app

    @classmethod
    def transition_stage(
        cls,
        db: Session,
        application_id: str,
        target_stage_key: str,
        comments: Optional[str],
        actor: User
    ) -> Application:
        app = db.get(Application, application_id)
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        # 1. Scoping checks
        if actor.role == UserRole.INST_ADMIN.value:
            enforce_institution_scope(actor, app.institution_id)
        elif actor.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.EVC_COORD.value]:
            enforce_region_scope(actor, app.region_id)
        elif actor.role in [UserRole.COMM_MEMBER.value, UserRole.COMMITTEE_MBR.value]:
            from backend.app.models.evc import EVCVisit, EVCExpert
            is_assigned = db.query(EVCVisit).join(EVCExpert).filter(
                EVCVisit.application_id == app.id,
                EVCExpert.contact_email == actor.email
            ).first() is not None
            if not is_assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Security violation: Committee members can only transition applications assigned to their inspection visits."
                )

        # 2. Statutory decision safeguard
        if target_stage_key in ("APPROVED", "REJECTED"):
            require_statutory_authority(actor)

        # 3. Permitted transitions validation
        route_map = ROUTE_TRANSITIONS.get(app.route, {})
        allowed_targets = route_map.get(app.status, [])
        if target_stage_key not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transition: Cannot move from '{app.status}' to '{target_stage_key}' in {app.route}. Allowed next stages: {allowed_targets}"
            )

        # 4. Role authorization for target stage
        allowed_roles = STAGE_ROLE_PERMISSIONS.get(target_stage_key, [])
        if allowed_roles and actor.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unauthorized: Role {actor.role} is not permitted to transition application to {target_stage_key}."
            )

        target_stage = cls.get_stage_by_key(db, app.route, target_stage_key)
        if not target_stage:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Target stage '{target_stage_key}' not found in route {app.route}")

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=target_stage.sla_days) if target_stage.sla_days > 0 else None

        # Record Application History
        history = ApplicationHistory(
            application_id=app.id,
            from_stage_id=app.current_stage_id,
            to_stage_id=target_stage.id,
            action=f"TRANSITION_TO_{target_stage_key}",
            actor_id=actor.id,
            comments=comments
        )
        db.add(history)

        prev_status = app.status
        app.current_stage_id = target_stage.id
        app.status = target_stage_key
        app.stage_entered_at = now
        app.current_sla_deadline = deadline

        # Append-only audit record
        audit_service.record_event(
            db=db,
            actor_role=actor.role,
            action=f"APPLICATION_TRANSITION_{target_stage_key}",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=actor.id,
            previous_state=prev_status,
            new_state=target_stage_key,
            details={"comments": comments, "route": app.route}
        )

        db.commit()
        db.refresh(app)
        return app

    @classmethod
    def return_for_deficiency(
        cls,
        db: Session,
        application_id: str,
        reason: str,
        actor: User
    ) -> Application:
        """
        Invariant INV-02: Returning an application for clarification requires a non-empty, audited rationale.
        """
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mandatory requirement: A clear, non-empty deficiency reason must be recorded when returning an application."
            )

        app = db.get(Application, application_id)
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        target_stage_key = "SCRUTINY_DEFICIENT"
        allowed_review_roles = [
            UserRole.RO_OFFICER.value,
            UserRole.REGIONAL_DIR.value,
            UserRole.BO_OFFICER.value,
            UserRole.BUREAU_OFFICER.value,
            UserRole.COMM_MEMBER.value,
            UserRole.COMMITTEE_MBR.value,
            UserRole.SYS_ADMIN.value
        ]
        if actor.role not in allowed_review_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unauthorized: Role {actor.role} is not permitted to return applications for deficiency."
            )

        if actor.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value]:
            enforce_region_scope(actor, app.region_id)
        elif actor.role in [UserRole.COMM_MEMBER.value, UserRole.COMMITTEE_MBR.value]:
            from backend.app.models.evc import EVCVisit, EVCExpert
            is_assigned = db.query(EVCVisit).join(EVCExpert).filter(
                EVCVisit.application_id == app.id,
                EVCExpert.contact_email == actor.email
            ).first() is not None
            if not is_assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Security violation: Committee members can only return applications assigned to their inspection visits."
                )
        target_stage = cls.get_stage_by_key(db, app.route, target_stage_key)
        if not target_stage:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stage {target_stage_key} not configured in route {app.route}")

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=target_stage.sla_days)

        history = ApplicationHistory(
            application_id=app.id,
            from_stage_id=app.current_stage_id,
            to_stage_id=target_stage.id,
            action="RETURN_FOR_DEFICIENCY",
            actor_id=actor.id,
            comments=reason
        )
        db.add(history)

        prev_status = app.status
        app.current_stage_id = target_stage.id
        app.status = target_stage_key
        app.stage_entered_at = now
        app.current_sla_deadline = deadline
        app.return_count += 1  # Incremented to track repeated returns in Exception Cockpit

        audit_service.record_event(
            db=db,
            actor_role=actor.role,
            action="APPLICATION_RETURNED_DEFICIENT",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=actor.id,
            previous_state=prev_status,
            new_state=target_stage_key,
            details={"deficiency_reason": reason, "return_count": app.return_count}
        )

        db.commit()
        db.refresh(app)
        return app

    @classmethod
    def resubmit_clarification(
        cls,
        db: Session,
        application_id: str,
        clarification_notes: str,
        actor: User
    ) -> Application:
        app = db.get(Application, application_id)
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        if actor.role != UserRole.INST_ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: Only the authorized Institution Administrator can resubmit clarification responses."
            )
        enforce_institution_scope(actor, app.institution_id)

        if app.status != "SCRUTINY_DEFICIENT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resubmit: Application is in '{app.status}', not in 'SCRUTINY_DEFICIENT'."
            )

        target_stage_key = "UNDER_SCRUTINY"
        target_stage = cls.get_stage_by_key(db, app.route, target_stage_key)
        if not target_stage:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stage {target_stage_key} not configured in route {app.route}")

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=target_stage.sla_days)

        history = ApplicationHistory(
            application_id=app.id,
            from_stage_id=app.current_stage_id,
            to_stage_id=target_stage.id,
            action="RESUBMIT_CLARIFICATION",
            actor_id=actor.id,
            comments=clarification_notes or "Clarification submitted by institution."
        )
        db.add(history)

        prev_status = app.status
        app.current_stage_id = target_stage.id
        app.status = target_stage_key
        app.stage_entered_at = now
        app.current_sla_deadline = deadline

        audit_service.record_event(
            db=db,
            actor_role=actor.role,
            action="APPLICATION_RESUBMITTED",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=actor.id,
            previous_state=prev_status,
            new_state=target_stage_key,
            details={"clarification_notes": clarification_notes, "return_count": app.return_count}
        )

        db.commit()
        db.refresh(app)
        return app

    @classmethod
    def reassign_officer(
        cls,
        db: Session,
        application_id: str,
        officer_id: str,
        comments: Optional[str],
        actor: User
    ) -> Application:
        app = db.get(Application, application_id)
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        allowed_reassign_roles = [
            UserRole.RO_OFFICER.value,
            UserRole.REGIONAL_DIR.value,
            UserRole.BO_OFFICER.value,
            UserRole.BUREAU_OFFICER.value,
            UserRole.SYS_ADMIN.value
        ]
        if actor.role not in allowed_reassign_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Security violation: Role {actor.role} is not authorized to reassign case officers."
            )

        if actor.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value]:
            enforce_region_scope(actor, app.region_id)

        officer = db.get(User, officer_id)
        if not officer or officer.role not in (UserRole.RO_OFFICER.value, UserRole.BO_OFFICER.value, UserRole.COMM_MEMBER.value):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned officer must be a verified Regional Officer, Bureau Officer, or Committee Member.")

        prev_officer_id = app.assigned_officer_id
        app.assigned_officer_id = officer.id

        history = ApplicationHistory(
            application_id=app.id,
            from_stage_id=app.current_stage_id,
            to_stage_id=app.current_stage_id,
            action="REASSIGN_OFFICER",
            actor_id=actor.id,
            comments=f"Reassigned to {officer.full_name} ({officer.role}). {comments or ''}"
        )
        db.add(history)

        audit_service.record_event(
            db=db,
            actor_role=actor.role,
            action="APPLICATION_OFFICER_REASSIGNED",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=actor.id,
            details={"previous_officer_id": prev_officer_id, "new_officer_id": officer.id, "reason": comments}
        )

        db.commit()
        db.refresh(app)
        return app


workflow_engine = WorkflowEngine()

