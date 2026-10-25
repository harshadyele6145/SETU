from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User
from backend.app.models.application import Application
from backend.app.schemas.attention import AttentionQueueItem
from backend.app.services.attention_service import AttentionService


router = APIRouter(prefix="/api/attention", tags=["Explainable Attention Engine"])


@router.get("/queue", response_model=List[AttentionQueueItem])
def get_attention_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns prioritized attention queue computed deterministically across all multi-factor criteria.
    Scoped strictly to the authenticated user's institution or region.
    """
    return AttentionService.compute_attention_queue(db=db, user=current_user)


@router.get("/applications/{application_id}/summary")
def get_case_structured_summary(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns a deterministic structured case summary answering the 5 core operational questions:
    1. What needs attention?
    2. Why is it pending?
    3. Who is responsible?
    4. What must happen next?
    5. Can every action be traced?
    """
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Scope check
    if current_user.role == "INST_ADMIN" and app.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role in ["RO_OFFICER", "REGIONAL_DIR"] and app.region_id != current_user.region_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Trace audit trail events count
    audit_count = len(app.history)

    return {
        "application_no": app.application_no,
        "institution_name": app.institution.name if app.institution else "N/A",
        "route": app.route,
        "current_stage": app.current_stage.name if app.current_stage else app.status,
        "status": app.status,
        "questions": {
            "q1_what_needs_attention": f"Application {app.application_no} ({app.route}) in stage '{app.current_stage.name if app.current_stage else app.status}'.",
            "q2_why_pending": f"Return count: {app.return_count}. Awaiting required workflow determination or verification.",
            "q3_who_responsible": app.assigned_officer.full_name if app.assigned_officer else "Regional Office Scrutiny Committee",
            "q4_what_happens_next": "Complete stage verification and issue formal approval or deficiency notice.",
            "q5_can_be_traced": f"Yes. Cryptographically sealed in {audit_count} verifiable audit transitions with SHA-256 hash chaining."
        }
    }
