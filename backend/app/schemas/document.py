from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class DocumentUploadMetadata(BaseModel):
    institution_id: str
    application_id: Optional[str] = None
    document_category: str
    title: str
    issue_date: date
    expiry_date: date
    previous_document_id: Optional[str] = None


class DocumentVerifyRequest(BaseModel):
    is_verified: bool
    comments: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    institution_id: str
    institution_name: Optional[str] = None
    application_id: Optional[str] = None
    application_no: Optional[str] = None
    document_category: str
    title: str
    issue_date: date
    expiry_date: date
    current_version: int
    status: str
    file_path: str
    file_size: int
    mime_type: str
    sha256_hash: str
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    previous_document_id: Optional[str] = None
    days_to_expiry: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
