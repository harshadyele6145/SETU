from datetime import date, datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.compliance import ComplianceObligation, ComplianceEvidence
from backend.app.models.institution import Institution
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.models.user import User
from backend.app.core.security import UserRole
from backend.app.schemas.compliance import (
    ComplianceObligationCreate,
    ComplianceObligationResponse,
    ComplianceEvidenceResponse,
    ComplianceVerificationRequest
)
from backend.app.services.auth_service import get_current_user, enforce_institution_scope
from backend.app.services.compliance_service import compliance_service

router = APIRouter(prefix="/api/compliance", tags=["Compliance Obligations & Evidence"])


def format_obligation_response(ob: ComplianceObligation) -> ComplianceObligationResponse:
    today = date.today()
    days_remaining = (ob.due_date - today).days

    evidences_resp = []
    for ev in ob.evidences:
        evidences_resp.append(
            ComplianceEvidenceResponse(
                id=ev.id,
                obligation_id=ev.obligation_id,
                file_name=ev.file_name,
                file_path=ev.file_path,
                file_size=ev.file_size,
                mime_type=ev.mime_type,
                sha256_hash=ev.sha256_hash,
                notes=ev.notes,
                submitted_by_name=ev.submitted_by.full_name if ev.submitted_by else None,
                submission_date=ev.submission_date,
                verification_status=ev.verification_status,
                verified_by_name=ev.verified_by.full_name if ev.verified_by else None,
                verified_at=ev.verified_at,
                rejection_reason=ev.rejection_reason
            )
        )

    return ComplianceObligationResponse(
        id=ob.id,
        application_id=ob.application_id,
        application_no=ob.application.application_no if ob.application else None,
        institution_id=ob.institution_id,
        institution_name=ob.institution.name if ob.institution else None,
        category=ob.category,
        title=ob.title,
        description=ob.description,
        condition_source=ob.condition_source,
        due_date=ob.due_date,
        status=ob.status,
        responsible_person=ob.responsible_person,
        reviewer_name=ob.reviewer.full_name if ob.reviewer else None,
        review_comments=ob.review_comments,
        closed_at=ob.closed_at,
        evidences=evidences_resp,
        days_remaining=days_remaining,
        created_at=ob.created_at,
        updated_at=ob.updated_at
    )


@router.get("/obligations", response_model=List[ComplianceObligationResponse])
def list_obligations(
    status: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stmt = select(ComplianceObligation)

    # Server-enforced scope boundary
    if current_user.role == UserRole.INST_ADMIN.value:
        if not current_user.institution_id:
            return []
        stmt = stmt.where(ComplianceObligation.institution_id == current_user.institution_id)
    elif current_user.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.EVC_COORD.value]:
        if not current_user.region_id:
            return []
        stmt = stmt.join(Institution, ComplianceObligation.institution_id == Institution.id).where(
            Institution.region_id == current_user.region_id
        )
    elif current_user.role in [UserRole.COMMITTEE_MBR.value, UserRole.COMM_MEMBER.value]:
        assigned_app_ids = [
            row[0] for row in db.query(EVCVisit.application_id)
            .join(EVCExpert)
            .filter(EVCExpert.contact_email == current_user.email)
            .all()
        ]
        if not assigned_app_ids:
            return []
        stmt = stmt.where(ComplianceObligation.application_id.in_(assigned_app_ids))
    elif institution_id:
        stmt = stmt.where(ComplianceObligation.institution_id == institution_id)

    if status:
        stmt = stmt.where(ComplianceObligation.status == status)

    stmt = stmt.order_by(ComplianceObligation.due_date.asc())
    obligations = db.execute(stmt).scalars().all()
    return [format_obligation_response(ob) for ob in obligations]


@router.post("/obligations", response_model=ComplianceObligationResponse, status_code=status.HTTP_201_CREATED)
def create_obligation(
    payload: ComplianceObligationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.INST_ADMIN.value:
        enforce_institution_scope(current_user, payload.institution_id)

    ob = compliance_service.create_obligation(
        db=db,
        institution_id=payload.institution_id,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        condition_source=payload.condition_source,
        responsible_person=payload.responsible_person,
        application_id=payload.application_id,
        actor=current_user
    )
    return format_obligation_response(ob)


@router.get("/obligations/{id}", response_model=ComplianceObligationResponse)
def get_obligation(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ob = db.get(ComplianceObligation, id)
    if not ob:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance obligation not found")

    # Scope validation
    if current_user.role == UserRole.INST_ADMIN.value:
        enforce_institution_scope(current_user, ob.institution_id)
    elif current_user.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.EVC_COORD.value]:
        if not current_user.region_id or not ob.institution or ob.institution.region_id != current_user.region_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Obligation outside your assigned region")
    elif current_user.role in [UserRole.COMMITTEE_MBR.value, UserRole.COMM_MEMBER.value]:
        assigned_app_ids = [
            row[0] for row in db.query(EVCVisit.application_id)
            .join(EVCExpert)
            .filter(EVCExpert.contact_email == current_user.email)
            .all()
        ]
        if not ob.application_id or ob.application_id not in assigned_app_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Not assigned to this obligation's inspection")

    return format_obligation_response(ob)


@router.post("/obligations/{id}/evidence", response_model=ComplianceEvidenceResponse)
async def submit_obligation_evidence(
    id: str,
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ob = db.get(ComplianceObligation, id)
    if not ob:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance obligation not found")

    if current_user.role == UserRole.INST_ADMIN.value:
        enforce_institution_scope(current_user, ob.institution_id)

    evidence = await compliance_service.submit_evidence(
        db=db,
        obligation_id=id,
        upload_file=file,
        notes=notes,
        actor=current_user
    )
    return ComplianceEvidenceResponse(
        id=evidence.id,
        obligation_id=evidence.obligation_id,
        file_name=evidence.file_name,
        file_path=evidence.file_path,
        file_size=evidence.file_size,
        mime_type=evidence.mime_type,
        sha256_hash=evidence.sha256_hash,
        notes=evidence.notes,
        submitted_by_name=current_user.full_name,
        submission_date=evidence.submission_date,
        verification_status=evidence.verification_status,
        verified_by_name=None,
        verified_at=None,
        rejection_reason=None
    )


@router.post("/evidence/{evidence_id}/verify", response_model=ComplianceEvidenceResponse)
def verify_evidence(
    evidence_id: str,
    payload: ComplianceVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evidence_obj = db.get(ComplianceEvidence, evidence_id)
    if not evidence_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence record not found")

    ob = evidence_obj.obligation
    if current_user.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.EVC_COORD.value]:
        if not current_user.region_id or not ob.institution or ob.institution.region_id != current_user.region_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cannot verify evidence outside assigned region")

    evidence = compliance_service.verify_evidence(
        db=db,
        evidence_id=evidence_id,
        is_approved=payload.is_approved,
        review_comments=payload.review_comments,
        reviewer=current_user
    )
    return ComplianceEvidenceResponse(
        id=evidence.id,
        obligation_id=evidence.obligation_id,
        file_name=evidence.file_name,
        file_path=evidence.file_path,
        file_size=evidence.file_size,
        mime_type=evidence.mime_type,
        sha256_hash=evidence.sha256_hash,
        notes=evidence.notes,
        submitted_by_name=evidence.submitted_by.full_name if evidence.submitted_by else None,
        submission_date=evidence.submission_date,
        verification_status=evidence.verification_status,
        verified_by_name=current_user.full_name,
        verified_at=evidence.verified_at,
        rejection_reason=evidence.rejection_reason
    )
