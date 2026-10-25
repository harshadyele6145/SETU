from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.audit import AuditEvent
from backend.app.models.user import User
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

