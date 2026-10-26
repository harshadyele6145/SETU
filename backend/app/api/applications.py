from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.application import Application, ApplicationHistory
from backend.app.models.institution import Institution
from backend.app.models.region import Region
from backend.app.models.user import User
from backend.app.models.compliance import ComplianceObligation
from backend.app.models.document import DocumentRegistry
from backend.app.models.audit import AuditEvent
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.core.security import UserRole
from backend.app.schemas.application import (
    ApplicationCreate,
    ApplicationTransitionRequest,
    ApplicationReturnRequest,
    ApplicationReassignRequest,
    ApplicationResponse,
    ApplicationDetailResponse,
    ApplicationHistoryItem,
    ApplicationAccountabilityResponse,
    PermittedAction,
    AccountabilityBlocker
)
from backend.app.services.auth_service import get_current_user, enforce_institution_scope, enforce_region_scope
from backend.app.services.workflow_engine import workflow_engine

router = APIRouter(prefix="/api/applications", tags=["Applications & Workflow Tracking"])


def ensure_utc(dt: Optional[datetime]) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def format_application_response(app: Application) -> ApplicationResponse:
    now = datetime.now(timezone.utc)
    stage_entered = ensure_utc(app.stage_entered_at or app.submitted_at or now)
    submitted = ensure_utc(app.submitted_at or now)

    days_in_stage = max(0, (now - stage_entered).days)
    total_days = max(0, (now - submitted).days)

    return ApplicationResponse(
        id=app.id,
        application_no=app.application_no,
        institution_id=app.institution_id,
        institution_name=app.institution.name if app.institution else None,
        institution_aicte_id=app.institution.aicte_id if app.institution else None,
        region_id=app.region_id,
        region_name=app.region.name if app.region else None,
        academic_year=app.academic_year,
        application_type=app.application_type,
        route=app.route,
        status=app.status,
        current_stage_key=app.current_stage.stage_key if app.current_stage else None,
        current_stage_name=app.current_stage.name if app.current_stage else None,
        assigned_officer_id=app.assigned_officer_id,
        assigned_officer_name=app.assigned_officer.full_name if app.assigned_officer else None,
        submitted_at=app.submitted_at or now,
        stage_entered_at=app.stage_entered_at or now,
        current_sla_deadline=app.current_sla_deadline,
        is_paused=app.is_paused,
        return_count=app.return_count,
        days_in_stage=days_in_stage,
        total_days=total_days
    )


@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    status: Optional[str] = Query(None),
    route: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stmt = select(Application)

    # Server-enforced scope boundary:
    # 1. Institution Administrator can only see own institution applications
    if current_user.role == UserRole.INST_ADMIN.value:
        if not current_user.institution_id:
            return []
        stmt = stmt.where(Application.institution_id == current_user.institution_id)
    # 2. Regional Roles (RO Officer, Regional Director, EVC Coord) can only see applications from their own region
    elif current_user.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.EVC_COORD.value]:
        if not current_user.region_id:
            return []
        stmt = stmt.where(Application.region_id == current_user.region_id)
    # 3. Committee Members only see applications linked to their assigned inspection visits
    elif current_user.role in [UserRole.COMMITTEE_MBR.value, UserRole.COMM_MEMBER.value]:
        from backend.app.models.evc import EVCVisit, EVCExpert
        assigned_ids = [
            row[0] for row in db.query(EVCVisit.application_id)
            .join(EVCExpert)
            .filter(EVCExpert.contact_email == current_user.email)
            .all()
        ]
        if not assigned_ids:
            return []
        stmt = stmt.where(Application.id.in_(assigned_ids))
    # 4. Cross-regional roles can filter optionally
    else:
        if institution_id:
            stmt = stmt.where(Application.institution_id == institution_id)
        if region_id:
            stmt = stmt.where(Application.region_id == region_id)

    if status:
        stmt = stmt.where(Application.status == status)
    if route:
        stmt = stmt.where(Application.route == route)

    stmt = stmt.order_by(desc(Application.submitted_at))
    apps = db.execute(stmt).scalars().all()

    return [format_application_response(a) for a in apps]


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.institution_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Creating an application requires an assigned institution."
        )

    app = workflow_engine.create_application(
        db=db,
        institution_id=current_user.institution_id,
        academic_year=payload.academic_year,
        application_type=payload.application_type,
        route=payload.route,
        actor=current_user
    )
    db.commit()
    db.refresh(app)
    return format_application_response(app)


@router.get("/{id}", response_model=ApplicationDetailResponse)
def get_application(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.get(Application, id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Scope validation
    if current_user.role == UserRole.INST_ADMIN.value:
        enforce_institution_scope(current_user, app.institution_id)
    elif current_user.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value]:
        enforce_region_scope(current_user, app.region_id)
    elif current_user.role in [UserRole.COMMITTEE_MBR.value, UserRole.COMM_MEMBER.value]:
        from backend.app.models.evc import EVCVisit, EVCExpert
        is_assigned = db.query(EVCVisit).join(EVCExpert).filter(
            EVCVisit.application_id == app.id,
            EVCExpert.contact_email == current_user.email
        ).first() is not None
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: Committee members can only view applications assigned to their inspection visits."
            )

    base_resp = format_application_response(app)

    history_items = []
    for h in app.history:
        history_items.append(
            ApplicationHistoryItem(
                id=h.id,
                action=h.action,
                actor_name=h.actor.full_name if h.actor else "System",
                actor_role=h.actor.role if h.actor else "SYSTEM",
                from_stage=h.from_stage.name if h.from_stage else None,
                to_stage=h.to_stage.name if h.to_stage else None,
                comments=h.comments,
                created_at=h.created_at
            )
        )

    return ApplicationDetailResponse(
        **base_resp.model_dump(),
        history=history_items
    )


@router.post("/{id}/submit", response_model=ApplicationResponse)
def submit_application(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = workflow_engine.submit_application(db, id, current_user)
    return format_application_response(app)


@router.post("/{id}/transition", response_model=ApplicationResponse)
def transition_application(
    id: str,
    payload: ApplicationTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_stage = payload.target_stage_key or payload.action
    app = workflow_engine.transition_stage(
        db=db,
        application_id=id,
        target_stage_key=target_stage,
        comments=payload.comments,
        actor=current_user
    )
    return format_application_response(app)


@router.post("/{id}/return", response_model=ApplicationResponse)
def return_application(
    id: str,
    payload: ApplicationReturnRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = workflow_engine.return_for_deficiency(
        db=db,
        application_id=id,
        reason=payload.comments,
        actor=current_user
    )
    return format_application_response(app)


@router.post("/{id}/resubmit", response_model=ApplicationResponse)
def resubmit_application(
    id: str,
    payload: ApplicationReturnRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = workflow_engine.resubmit_clarification(
        db=db,
        application_id=id,
        clarification_notes=payload.comments,
        actor=current_user
    )
    return format_application_response(app)


@router.post("/{id}/reassign", response_model=ApplicationResponse)
def reassign_application(
    id: str,
    payload: ApplicationReassignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = workflow_engine.reassign_officer(
        db=db,
        application_id=id,
        officer_id=payload.officer_id,
        comments=payload.comments,
        actor=current_user
    )
    return format_application_response(app)


@router.get("/{id}/timeline", response_model=List[ApplicationHistoryItem])
def get_application_timeline(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.get(Application, id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if current_user.role == UserRole.INST_ADMIN.value:
        enforce_institution_scope(current_user, app.institution_id)
    elif current_user.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.EVC_COORD.value]:
        enforce_region_scope(current_user, app.region_id)
    elif current_user.role in [UserRole.COMMITTEE_MBR.value, UserRole.COMM_MEMBER.value]:
        from backend.app.models.evc import EVCVisit, EVCExpert
        is_assigned = db.query(EVCVisit).join(EVCExpert).filter(
            EVCVisit.application_id == app.id,
            EVCExpert.contact_email == current_user.email
        ).first() is not None
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: Committee members can only view timeline of applications assigned to their inspection visits."
            )

    stmt = select(ApplicationHistory).where(ApplicationHistory.application_id == id).order_by(desc(ApplicationHistory.created_at))
    history = db.execute(stmt).scalars().all()

    return [
        ApplicationHistoryItem(
            id=h.id,
            action=h.action,
            actor_name=h.actor.full_name if h.actor else "System",
            actor_role=h.actor.role if h.actor else "SYSTEM",
            from_stage=h.from_stage.name if h.from_stage else None,
            to_stage=h.to_stage.name if h.to_stage else None,
            comments=h.comments,
            created_at=h.created_at
        )
        for h in history
    ]


@router.get("/{id}/accountability", response_model=ApplicationAccountabilityResponse)
def get_application_accountability(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.get(Application, id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Scope check
    if current_user.role == UserRole.INST_ADMIN.value:
        enforce_institution_scope(current_user, app.institution_id)
    elif current_user.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.EVC_COORD.value]:
        enforce_region_scope(current_user, app.region_id)
    elif current_user.role in [UserRole.COMMITTEE_MBR.value, UserRole.COMM_MEMBER.value]:
        is_assigned = db.query(EVCVisit).join(EVCExpert).filter(
            EVCVisit.application_id == app.id,
            EVCExpert.contact_email == current_user.email
        ).first() is not None
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: Committee members can only view applications assigned to their inspection visits."
            )

    now = datetime.now(timezone.utc)
    stage_at = ensure_utc(app.stage_entered_at or app.submitted_at or now)
    days_in_stage = max(0, (now - stage_at).days)
    sla_days = app.current_stage.sla_days if app.current_stage and app.current_stage.sla_days else 15
    deadline = app.current_sla_deadline or (stage_at + timedelta(days=sla_days))
    deadline_utc = ensure_utc(deadline) if deadline else None
    days_remaining = (deadline_utc - now).days if deadline_utc else (sla_days - days_in_stage)
    is_overdue = days_remaining < 0

    # Holding party determination
    if app.status in ["DRAFT", "PENDING_CLARIFICATION", "SCRUTINY_DEFICIENT", "DEFICIENCY_COMMUNICATED"]:
        holding_party = "WAITING_ON_INSTITUTION"
        holding_party_label = "Pending Institutional Action / Resubmission"
        holding_responsible_role = "INST_ADMIN"
    else:
        holding_party = "WAITING_ON_AICTE"
        holding_party_label = "Under AICTE Statutory Operations"
        if app.status == "SUBMITTED":
            holding_responsible_role = "RO_OFFICER"
        elif app.status == "UNDER_SCRUTINY":
            holding_responsible_role = "RO_OFFICER"
        elif app.status in ["SCRUTINY_RECOMMENDED", "AWAITING_EVC", "EVC_QUEUE"]:
            holding_responsible_role = "EVC_COORD"
        elif app.status == "EVC_SCHEDULED":
            holding_responsible_role = "COMMITTEE_MBR"
        elif app.status in ["EVC_COMPLETED", "EVC_REPORT_SUBMITTED"]:
            holding_responsible_role = "RO_OFFICER"
        elif app.status in ["SAC_RECOMMENDED", "SHC_SCHEDULED", "DECISION_PENDING"]:
            holding_responsible_role = "COMP_AUTH"
        else:
            holding_responsible_role = "RO_OFFICER"

    # Define permitted candidate actions based on current status
    candidate_actions = []
    if app.status == "DRAFT":
        candidate_actions.append({
            "action_key": "SUBMIT_APPLICATION",
            "action_label": "Formally Submit Application Dossier",
            "target_stage_key": "SUBMITTED",
            "endpoint": f"/api/applications/{app.id}/submit",
            "allowed_roles": ["INST_ADMIN"],
            "description": "Commit finalized institutional application dossier to initiate regional intake."
        })
    elif app.status == "SUBMITTED":
        candidate_actions.append({
            "action_key": "START_SCRUTINY",
            "action_label": "Initiate Document Scrutiny",
            "target_stage_key": "UNDER_SCRUTINY",
            "endpoint": f"/api/applications/{app.id}/transition",
            "allowed_roles": ["RO_OFFICER", "REGIONAL_DIR", "SYS_ADMIN"],
            "description": "Convene Document Scrutiny Committee and verify affidavits, land deeds, and approvals."
        })
        candidate_actions.append({
            "action_key": "REASSIGN_OFFICER",
            "action_label": "Reassign Scrutiny Officer",
            "target_stage_key": None,
            "endpoint": f"/api/applications/{app.id}/reassign",
            "allowed_roles": ["RO_OFFICER", "REGIONAL_DIR", "BO_OFFICER", "BUREAU_OFFICER", "SYS_ADMIN"],
            "description": "Transfer case file responsibility to another designated regional scrutiny officer."
        })
    elif app.status == "UNDER_SCRUTINY":
        next_target = "SCRUTINY_RECOMMENDED" if app.route == "ROUTE_A" else "EVC_QUEUE"
        candidate_actions.append({
            "action_key": "CLEAR_SCRUTINY",
            "action_label": "Clear Scrutiny & Recommend Forward",
            "target_stage_key": next_target,
            "endpoint": f"/api/applications/{app.id}/transition",
            "allowed_roles": ["RO_OFFICER", "REGIONAL_DIR", "SYS_ADMIN"],
            "description": f"Confirm all documentary requirements are met and advance application to {next_target}."
        })
        candidate_actions.append({
            "action_key": "RETURN_DEFICIENCY",
            "action_label": "Issue Formal Deficiency Return",
            "target_stage_key": "SCRUTINY_DEFICIENT",
            "endpoint": f"/api/applications/{app.id}/return",
            "allowed_roles": ["RO_OFFICER", "REGIONAL_DIR", "SYS_ADMIN"],
            "description": "Return dossier to institution with mandatory statutory reasons for documentary cure."
        })
    elif app.status in ["SCRUTINY_DEFICIENT", "DEFICIENCY_COMMUNICATED", "PENDING_CLARIFICATION"]:
        candidate_actions.append({
            "action_key": "RESUBMIT_CLARIFICATION",
            "action_label": "Resubmit Dossier with Deficiency Cures",
            "target_stage_key": "UNDER_SCRUTINY",
            "endpoint": f"/api/applications/{app.id}/resubmit",
            "allowed_roles": ["INST_ADMIN"],
            "description": "Upload rectified documents and submit response to deficiency observations."
        })
    elif app.status in ["SCRUTINY_RECOMMENDED", "AWAITING_EVC", "EVC_QUEUE"]:
        candidate_actions.append({
            "action_key": "SCHEDULE_EVC",
            "action_label": "Schedule 3-Member EVC Inspection",
            "target_stage_key": "EVC_SCHEDULED",
            "endpoint": f"/api/applications/{app.id}/transition",
            "allowed_roles": ["EVC_COORD", "SYS_ADMIN"],
            "description": "Constitute 3-member expert committee roster from peer institutions and fix physical inspection date."
        })
    elif app.status == "EVC_SCHEDULED":
        candidate_actions.append({
            "action_key": "COMPLETE_EVC",
            "action_label": "Submit Physical Inspection Report",
            "target_stage_key": "EVC_COMPLETED",
            "endpoint": f"/api/applications/{app.id}/transition",
            "allowed_roles": ["COMMITTEE_MBR", "COMM_MEMBER", "EVC_COORD", "SYS_ADMIN"],
            "description": "Upload verified geo-tagged inspection checklist, lab equipment receipts, and sign off."
        })
    elif app.status in ["EVC_COMPLETED", "EVC_REPORT_SUBMITTED"]:
        candidate_actions.append({
            "action_key": "FORWARD_TO_COMP_AUTH",
            "action_label": "Forward EVC Findings for Final Decision",
            "target_stage_key": "DECISION_PENDING",
            "endpoint": f"/api/applications/{app.id}/transition",
            "allowed_roles": ["RO_OFFICER", "REGIONAL_DIR", "BO_OFFICER", "BUREAU_OFFICER", "SYS_ADMIN"],
            "description": "Compile regional inspection summary and transmit to Competent Authority for determination."
        })
        candidate_actions.append({
            "action_key": "RETURN_EVC_DEFICIENCY",
            "action_label": "Issue Physical Non-Compliance Notice",
            "target_stage_key": "SCRUTINY_DEFICIENT",
            "endpoint": f"/api/applications/{app.id}/return",
            "allowed_roles": ["RO_OFFICER", "REGIONAL_DIR", "SYS_ADMIN"],
            "description": "Issue notice regarding infrastructural or laboratory deficiencies observed during campus visit."
        })
    elif app.status in ["DECISION_PENDING", "SAC_RECOMMENDED"]:
        candidate_actions.append({
            "action_key": "STATUTORY_APPROVE",
            "action_label": "Grant AICTE Statutory Approval",
            "target_stage_key": "APPROVED",
            "endpoint": f"/api/applications/{app.id}/transition",
            "allowed_roles": ["COMP_AUTH", "SYS_ADMIN"],
            "description": "Exercise exclusive statutory authority to issue formal Council Approval Order."
        })
        candidate_actions.append({
            "action_key": "STATUTORY_REJECT",
            "action_label": "Issue Statutory Rejection Order",
            "target_stage_key": "REJECTED",
            "endpoint": f"/api/applications/{app.id}/transition",
            "allowed_roles": ["COMP_AUTH", "SYS_ADMIN"],
            "description": "Formally reject application citing persistent non-compliance with APH norms."
        })

    # Evaluate action permissions for the authenticated user
    permitted_actions: List[PermittedAction] = []
    user_can_act = False

    for ca in candidate_actions:
        role_matches = (
            current_user.role in ca["allowed_roles"] or
            (current_user.role == "BUREAU_OFFICER" and "BO_OFFICER" in ca["allowed_roles"]) or
            (current_user.role == "COMMITTEE_MBR" and "COMM_MEMBER" in ca["allowed_roles"]) or
            (current_user.role == "COMP_REV" and "COMP_REVIEW" in ca["allowed_roles"])
        )

        scope_matches = True
        if current_user.role == "INST_ADMIN":
            scope_matches = (current_user.institution_id == app.institution_id)
        elif current_user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            scope_matches = (current_user.region_id == app.region_id)
        elif current_user.role in ["COMM_MEMBER", "COMMITTEE_MBR"]:
            is_assigned = db.query(EVCVisit).join(EVCExpert).filter(
                EVCVisit.application_id == app.id,
                EVCExpert.contact_email == current_user.email
            ).first() is not None
            scope_matches = is_assigned

        is_allowed = role_matches and scope_matches
        if is_allowed:
            user_can_act = True

        permitted_actions.append(PermittedAction(
            action_key=ca["action_key"],
            action_label=ca["action_label"],
            target_stage_key=ca["target_stage_key"],
            endpoint=ca["endpoint"],
            http_method="POST",
            allowed_roles=ca["allowed_roles"],
            is_permitted_for_user=is_allowed,
            description=ca["description"]
        ))

    # Evaluate Attention Factors and composite score
    attention_score = 0
    attention_factors: List[str] = []

    if is_overdue:
        overdue_days = abs(days_remaining)
        pts = min(40, 25 + (overdue_days * 2))
        attention_score += pts
        attention_factors.append(f"SLA Breach: Overdue by {overdue_days} days (+{pts} pts)")
    elif days_remaining <= 2:
        attention_score += 25
        attention_factors.append(f"Urgent SLA Window: Expires in {days_remaining} days (+25 pts)")
    elif days_remaining <= 7:
        attention_score += 15
        attention_factors.append(f"Approaching Deadline: {days_remaining} days remaining (+15 pts)")

    if app.return_count >= 2:
        attention_score += 20
        attention_factors.append(f"Chronic Returns: Case returned {app.return_count} times (+20 pts)")
    elif app.return_count == 1:
        attention_score += 10
        attention_factors.append("Previous Deficiency Return: Returned once for clarification (+10 pts)")

    if not app.assigned_officer_id and app.status not in ["DRAFT", "APPROVED", "REJECTED"]:
        attention_score += 10
        attention_factors.append("Unassigned Officer: Case lacks dedicated scrutiny officer (+10 pts)")

    # Query blockers
    blockers: List[AccountabilityBlocker] = []
    linked_obs = db.query(ComplianceObligation).filter(
        ComplianceObligation.application_id == app.id,
        ComplianceObligation.status.in_(["OVERDUE", "DEFICIENT", "DUE_SOON"])
    ).all()
    for o in linked_obs:
        sev = "CRITICAL" if o.status == "OVERDUE" else ("HIGH" if o.status == "DEFICIENT" else "MEDIUM")
        blockers.append(AccountabilityBlocker(
            type="COMPLIANCE",
            title=o.title,
            status=o.status,
            detail=f"{o.category} - {o.description or ''}",
            severity=sev
        ))
        if o.status == "OVERDUE":
            attention_score += 20
            attention_factors.append("Mandatory compliance undertaking is overdue (+20 pts)")

    expired_docs = db.query(DocumentRegistry).filter(
        DocumentRegistry.institution_id == app.institution_id,
        DocumentRegistry.status.in_(["EXPIRED", "EXPIRING_SOON"])
    ).all()
    for d in expired_docs:
        sev = "CRITICAL" if d.status == "EXPIRED" else "MEDIUM"
        blockers.append(AccountabilityBlocker(
            type="DOCUMENT",
            title=d.title,
            status=d.status,
            detail=f"Category: {d.document_category}, Expires: {d.expiry_date}",
            severity=sev
        ))
        if d.status == "EXPIRED":
            attention_score += 15
            attention_factors.append("Prescribed statutory lease/safety certificate expired (+15 pts)")

    if attention_score >= 70:
        attention_tier = "CRITICAL"
    elif attention_score >= 45:
        attention_tier = "HIGH"
    elif attention_score >= 25:
        attention_tier = "MEDIUM"
    else:
        attention_tier = "LOW"

    # Audit trail summary
    audit_events = db.query(AuditEvent).filter(AuditEvent.entity_id == app.id).order_by(desc(AuditEvent.sequence_no)).all()
    audit_count = len(audit_events)
    latest_hash = audit_events[0].current_hash if audit_events else None

    return ApplicationAccountabilityResponse(
        application_id=app.id,
        application_no=app.application_no,
        institution_name=app.institution.name if app.institution else "N/A",
        institution_aicte_id=app.institution.aicte_id if app.institution else None,
        region_name=app.region.name if app.region else "N/A",
        route=app.route,
        status=app.status,
        current_stage_name=app.current_stage.name if app.current_stage else app.status,
        stage_entered_at=stage_at,
        days_in_stage=days_in_stage,
        sla_limit_days=sla_days,
        deadline=deadline_utc,
        days_remaining=days_remaining,
        is_overdue=is_overdue,
        holding_party=holding_party,
        holding_party_label=holding_party_label,
        holding_responsible_role=holding_responsible_role,
        assigned_officer_name=app.assigned_officer.full_name if app.assigned_officer else None,
        return_count=app.return_count,
        current_user_role=current_user.role,
        current_user_can_act=user_can_act,
        permitted_next_actions=permitted_actions,
        attention_score=min(100, attention_score),
        attention_tier=attention_tier,
        attention_factors=attention_factors[:4],
        blockers=blockers,
        audit_event_count=audit_count,
        latest_audit_hash=latest_hash
    )
