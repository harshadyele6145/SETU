from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from backend.app.core.database import get_db
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.services.evc_service import EVCService


router = APIRouter(prefix="/api/evc", tags=["Expert Visit Committee (EVC)"])


class EVCExpertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    expert_name: str
    designation: str
    organization: str
    contact_email: str
    status: str


class EVCVisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    application_no: str
    institution_name: str
    region_name: str
    status: str
    proposed_date: Optional[date] = None
    confirmed_date: Optional[date] = None
    completed_date: Optional[date] = None
    report_submitted_date: Optional[date] = None
    coordinator_id: Optional[str] = None
    coordinator_name: Optional[str] = None
    delay_reason: Optional[str] = None
    report_summary: Optional[str] = None
    report_file_ref: Optional[str] = None
    experts: List[EVCExpertOut] = []
    created_at: datetime


class ScheduleVisitRequest(BaseModel):
    application_id: str
    proposed_date: str  # YYYY-MM-DD
    coordinator_id: Optional[str] = None


class RescheduleVisitRequest(BaseModel):
    new_date: str  # YYYY-MM-DD
    delay_reason: str  # Mandatory justification


class AssignExpertRequest(BaseModel):
    expert_name: str
    designation: str
    organization: str
    contact_email: str


def format_visit(v: EVCVisit) -> EVCVisitOut:
    app = v.application
    inst = app.institution if app else None
    reg = app.region if app else None
    return EVCVisitOut(
        id=v.id,
        application_id=v.application_id,
        application_no=app.application_no if app else "UNKNOWN",
        institution_name=inst.name if inst else "Unknown Institution",
        region_name=reg.name if reg else "Unknown Region",
        status=v.status,
        proposed_date=v.proposed_date,
        confirmed_date=v.confirmed_date,
        completed_date=v.completed_date,
        report_submitted_date=v.report_submitted_date,
        coordinator_id=v.coordinator_id,
        coordinator_name=v.coordinator.full_name if v.coordinator else None,
        delay_reason=v.delay_reason,
        report_summary=v.report_summary,
        report_file_ref=v.report_file_ref,
        experts=[EVCExpertOut.model_validate(e) for e in v.experts],
        created_at=v.created_at
    )


@router.get("/visits", response_model=List[EVCVisitOut])
def list_visits(
    status_filter: Optional[str] = Query(None, alias="status"),
    region_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    visits = EVCService.get_scoped_visits(
        db=db,
        user=current_user,
        status=status_filter,
        region_id=region_id
    )
    return [format_visit(v) for v in visits]


@router.post("/visits", response_model=EVCVisitOut, status_code=status.HTTP_201_CREATED)
def schedule_visit(
    payload: ScheduleVisitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        dt = date.fromisoformat(payload.proposed_date)
        visit = EVCService.schedule_visit(
            db=db,
            application_id=payload.application_id,
            proposed_date=dt,
            coordinator_id=payload.coordinator_id,
            user=current_user
        )
        return format_visit(visit)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/visits/{visit_id}/reschedule", response_model=EVCVisitOut)
def reschedule_visit(
    visit_id: str,
    payload: RescheduleVisitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        dt = date.fromisoformat(payload.new_date)
        visit = EVCService.reschedule_visit(
            db=db,
            visit_id=visit_id,
            new_date=dt,
            delay_reason=payload.delay_reason,
            user=current_user
        )
        return format_visit(visit)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/visits/{visit_id}/experts", response_model=EVCExpertOut, status_code=status.HTTP_201_CREATED)
def assign_expert(
    visit_id: str,
    payload: AssignExpertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        expert = EVCService.assign_expert(
            db=db,
            visit_id=visit_id,
            expert_name=payload.expert_name,
            designation=payload.designation,
            organization=payload.organization,
            contact_email=payload.contact_email,
            user=current_user
        )
        return EVCExpertOut.model_validate(expert)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/visits/{visit_id}/report", response_model=EVCVisitOut)
async def submit_evc_report(
    visit_id: str,
    report_summary: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        content = await file.read()
        visit = EVCService.submit_report(
            db=db,
            visit_id=visit_id,
            report_summary=report_summary,
            file_bytes=content,
            file_name=file.filename or "evc_report.pdf",
            user=current_user
        )
        return format_visit(visit)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
