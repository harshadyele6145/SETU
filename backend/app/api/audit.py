from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, or_
from backend.app.core.database import get_db
from backend.app.models.audit import AuditEvent
from backend.app.models.user import User
from backend.app.models.application import Application
from backend.app.models.compliance import ComplianceObligation
from backend.app.models.document import DocumentRegistry
from backend.app.models.institution import Institution
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.core.security import UserRole, is_role_in, normalize_role
from backend.app.schemas.audit import AuditEventResponse, AuditChainVerificationResult
from backend.app.services.auth_service import get_current_user
from backend.app.services.audit_service import audit_service

router = APIRouter(prefix="/api/audit", tags=["Cryptographic Audit Trail"])


@router.get("", response_model=List[AuditEventResponse])
def list_audit_events(
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stmt = select(AuditEvent)

    # Multi-tenant data isolation on audit events
    if normalize_role(current_user.role) == UserRole.INST_ADMIN.value:
        if not current_user.institution_id:
            return []
        inst_app_ids = [row[0] for row in db.query(Application.id).filter(Application.institution_id == current_user.institution_id).all()]
        inst_ob_ids = [row[0] for row in db.query(ComplianceObligation.id).filter(ComplianceObligation.institution_id == current_user.institution_id).all()]
        inst_doc_ids = [row[0] for row in db.query(DocumentRegistry.id).filter(DocumentRegistry.institution_id == current_user.institution_id).all()]
        allowed_ids = set(inst_app_ids + inst_ob_ids + inst_doc_ids + [current_user.institution_id])
        stmt = stmt.where(or_(AuditEvent.entity_id.in_(allowed_ids), AuditEvent.actor_id == current_user.id))

    elif is_role_in(current_user.role, [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.EVC_COORD.value]):
        if not current_user.region_id:
            return []
        reg_app_ids = [row[0] for row in db.query(Application.id).filter(Application.region_id == current_user.region_id).all()]
        reg_inst_ids = [row[0] for row in db.query(Institution.id).filter(Institution.region_id == current_user.region_id).all()]
        allowed_ids = set(reg_app_ids + reg_inst_ids)
        stmt = stmt.where(or_(AuditEvent.entity_id.in_(allowed_ids), AuditEvent.actor_id == current_user.id))

    elif is_role_in(current_user.role, [UserRole.COMMITTEE_MBR.value, UserRole.COMM_MEMBER.value]):
        assigned_app_ids = [
            row[0] for row in db.query(EVCVisit.application_id)
            .join(EVCExpert)
            .filter(EVCExpert.contact_email == current_user.email)
            .all()
        ]
        if not assigned_app_ids:
            return []
        stmt = stmt.where(or_(AuditEvent.entity_id.in_(assigned_app_ids), AuditEvent.actor_id == current_user.id))

    if entity_type:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    if action:
        stmt = stmt.where(AuditEvent.action == action)

    stmt = stmt.order_by(desc(AuditEvent.sequence_no)).offset(offset).limit(limit)
    events = db.execute(stmt).scalars().all()
    return events


@router.get("/verify-chain", response_model=AuditChainVerificationResult)
def verify_audit_hash_chain(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifies the cryptographic integrity of the append-only SHA-256 audit hash chain.
    """
    is_valid, total_checked, broken_seq, msg = audit_service.verify_chain(db)
    return AuditChainVerificationResult(
        is_valid=is_valid,
        total_events_checked=total_checked,
        genesis_hash_valid=True,
        broken_sequence_no=broken_seq,
        verification_message=msg,
        checked_at=datetime.now(timezone.utc)
    )

