from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ComplianceObligationCreate(BaseModel):
    application_id: Optional[str] = None
    institution_id: str
    category: str
    title: str
    description: str
    condition_source: str = "APH Condition Precedent"
    due_date: date
    responsible_person: Optional[str] = None


class ComplianceEvidenceResponse(BaseModel):
    id: str
    obligation_id: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    sha256_hash: str
    notes: Optional[str] = None
    submitted_by_name: Optional[str] = None
    submission_date: datetime
    verification_status: str
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ComplianceVerificationRequest(BaseModel):
    is_approved: bool
    review_comments: str  # Mandatory comments whether approved or marked deficient


class ComplianceObligationResponse(BaseModel):
    id: str
    application_id: Optional[str] = None
    application_no: Optional[str] = None
    institution_id: str
    institution_name: Optional[str] = None
    category: str
    title: str
    description: str
    condition_source: str
    due_date: date
    status: str
    responsible_person: Optional[str] = None
    reviewer_name: Optional[str] = None
    review_comments: Optional[str] = None
    closed_at: Optional[datetime] = None
    evidences: List[ComplianceEvidenceResponse] = []
    days_remaining: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
