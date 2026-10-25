from datetime import date, datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List


class ExpertCreate(BaseModel):
    expert_name: str
    designation: str
    organization: str
    contact_email: EmailStr


class ExpertResponse(BaseModel):
    id: str
    expert_name: str
    designation: str
    organization: str
    contact_email: str
    status: str

    class Config:
        from_attributes = True


class EVCScheduleRequest(BaseModel):
    proposed_date: date
    confirmed_date: Optional[date] = None
    coordinator_id: Optional[str] = None
    experts: List[ExpertCreate] = []


class EVCRescheduleRequest(BaseModel):
    new_date: date
    delay_reason: str


class EVCCompleteRequest(BaseModel):
    completed_date: date
    summary: str


class EVCReportSubmitRequest(BaseModel):
    report_summary: str
    report_file_ref: Optional[str] = None


class EVCVisitResponse(BaseModel):
    id: str
    application_id: str
    application_no: Optional[str] = None
    institution_name: Optional[str] = None
    region_name: Optional[str] = None
    status: str
    proposed_date: Optional[date] = None
    confirmed_date: Optional[date] = None
    completed_date: Optional[date] = None
    report_submitted_date: Optional[date] = None
    report_summary: Optional[str] = None
    coordinator_name: Optional[str] = None
    delay_reason: Optional[str] = None
    report_file_ref: Optional[str] = None
    experts: List[ExpertResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
