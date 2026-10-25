from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.application import Application, ApplicationHistory
from backend.app.models.institution import Institution
from backend.app.models.region import Region
from backend.app.models.user import User
from backend.app.core.security import UserRole
from backend.app.schemas.application import (
    ApplicationCreate,
    ApplicationTransitionRequest,
    ApplicationReturnRequest,
    ApplicationReassignRequest,
    ApplicationResponse,
    ApplicationDetailResponse,
    ApplicationHistoryItem
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
    elif current_user.role == UserRole.RO_OFFICER.value:
        enforce_region_scope(current_user, app.region_id)

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
