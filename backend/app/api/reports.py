import io
import csv
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User
from backend.app.models.application import Application
from backend.app.models.base import utc_now


router = APIRouter(prefix="/api/reports", tags=["Pendency Reports & Analytics"])


def format_pendency_data(apps: List[Application]):
    now = utc_now()
    results = []
    for a in apps:
        sub_at = a.submitted_at if a.submitted_at.tzinfo else a.submitted_at.replace(tzinfo=timezone.utc)
        stg_at = a.stage_entered_at if a.stage_entered_at.tzinfo else a.stage_entered_at.replace(tzinfo=timezone.utc)
        
        total_age = max(0, (now - sub_at).days)
        stage_age = max(0, (now - stg_at).days)
        sla_limit = a.current_stage.sla_days if a.current_stage else 15
        is_overdue = stage_age > sla_limit

        holding = "INSTITUTION" if a.status in ["DRAFT", "PENDING_CLARIFICATION"] else "AICTE_INTERNAL"

        results.append({
            "id": a.id,
            "application_no": a.application_no,
            "institution_name": a.institution.name if a.institution else "N/A",
            "region_name": a.region.name if a.region else "N/A",
            "route": a.route,
            "status": a.status,
            "current_stage": a.current_stage.name if a.current_stage else "Processing",
            "sla_limit_days": sla_limit,
            "stage_age_days": stage_age,
            "total_age_days": total_age,
            "is_overdue": is_overdue,
            "holding_party": holding,
            "return_count": a.return_count
        })
    return results


@router.get("/pendency")
def get_pendency_report(
    status: Optional[str] = None,
    route: Optional[str] = None,
    region_id: Optional[str] = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Application).filter(Application.status.notin_(["APPROVED", "REJECTED"]))

    # Scope enforcement
    if current_user.role == "INST_ADMIN":
        query = query.filter(Application.institution_id == current_user.institution_id)
    elif current_user.role in ["RO_OFFICER", "REGIONAL_DIR"]:
        query = query.filter(Application.region_id == current_user.region_id)

    if status:
        query = query.filter(Application.status == status)
    if route:
        query = query.filter(Application.route == route)
    if region_id and current_user.role not in ["INST_ADMIN", "RO_OFFICER", "REGIONAL_DIR"]:
        query = query.filter(Application.region_id == region_id)

    apps = query.order_by(desc(Application.stage_entered_at)).all()
    data = format_pendency_data(apps)

    if overdue_only:
        data = [d for d in data if d["is_overdue"]]

    return data


@router.get("/export")
def export_pendency_csv(
    status: Optional[str] = None,
    route: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exports pendency records to CSV with strict server-enforced scoping.
    """
    query = db.query(Application).filter(Application.status.notin_(["APPROVED", "REJECTED"]))

    if current_user.role == "INST_ADMIN":
        query = query.filter(Application.institution_id == current_user.institution_id)
    elif current_user.role in ["RO_OFFICER", "REGIONAL_DIR"]:
        query = query.filter(Application.region_id == current_user.region_id)

    if status:
        query = query.filter(Application.status == status)
    if route:
        query = query.filter(Application.route == route)

    apps = query.order_by(desc(Application.stage_entered_at)).all()
    rows = format_pendency_data(apps)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Application No",
        "Institution Name",
        "Region",
        "Route",
        "Status",
        "Current Stage",
        "Stage Age (Days)",
        "SLA Limit (Days)",
        "Is Overdue",
        "Holding Responsibility",
        "Return Count"
    ])

    for r in rows:
        writer.writerow([
            r["application_no"],
            r["institution_name"],
            r["region_name"],
            r["route"],
            r["status"],
            r["current_stage"],
            r["stage_age_days"],
            r["sla_limit_days"],
            "YES" if r["is_overdue"] else "NO",
            r["holding_party"],
            r["return_count"]
        ])

    output.seek(0)
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=setu_pendency_report.csv"
    return response
